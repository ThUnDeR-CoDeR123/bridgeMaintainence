from typing import Dict, List, Tuple
import statistics
import random
import math
import datetime
from typing import List, Dict, Any
from app.database import get_db
from app.models import Prediction
from app.crud import get_historial_data
def translate_sensors_to_model_input(
    current_data: Dict[str, str],
    historical_data: List[Dict[str, str]] = None
) -> Dict[str, float]:
    """
    Translates sensor data into degradation model parameters:
    - healthIndex
    - meanRate
    - stdRate

    Parameters
    ----------
    current_data : dict
        {
            "temperature": "32.61",
            "vibration": "0",
            "pressure": "1002.11"
        }

    historical_data : list of dicts (optional)
        [
            {"temperature": "29.1", "vibration": "1", "pressure": "1004.2"},
            ...
        ]

    Returns
    -------
    Tuple[healthIndex, meanRate, stdRate] : (float, float, float)
    """
    print("# Parse and validate")
    temperature = float(current_data.get("temperature", 25))
    vibration = int(float(current_data.get("vibration", 0)))
    pressure = float(current_data.get("pressure", 1010))

    print("# Base degradation assumptions")
    base_health_index = 100.0
    base_mean_rate = 0.1
    base_std_rate = 0.02

    print("# Penalty for bad conditions")
    temp_penalty = max(0, (temperature - 30) * 0.5) if temperature > 30 else max(0, (20 - temperature) * 0.3)
    pressure_penalty = max(0, (1000 - pressure) * 0.1) if pressure < 1000 else max(0, (pressure - 1020) * 0.05)
    vibration_penalty = 2.0 if vibration else 0.0

    total_penalty = temp_penalty + pressure_penalty + vibration_penalty
    health_index = max(0.0, base_health_index - total_penalty)

    print("# Rate increases with environmental stress")
    mean_rate = base_mean_rate + (total_penalty * 0.01)

    print("# Std deviation increases with deviation from ideal conditions")
    temp_deviation = abs(temperature - 25) * 0.001
    pressure_deviation = abs(pressure - 1010) * 0.0005
    vibration_noise = 0.01 if vibration else 0.0

    std_rate = base_std_rate + temp_deviation + pressure_deviation + vibration_noise

    print("# Optionally adjust using historical trends")
    if historical_data and len(historical_data) >= 2:
        temps = [float(d["temperature"]) for d in historical_data]
        pressures = [float(d["pressure"]) for d in historical_data]
        vibrations = [int(float(d["vibration"])) for d in historical_data]

        temp_trend = calculate_trend(temps)
        pressure_trend = calculate_trend(pressures)
        vibration_rate = sum(vibrations) / len(vibrations)

        print("# Adjust degradation rate based on trend severity")
        trend_adjustment = abs(temp_trend) * 0.01 + abs(pressure_trend) * 0.001 + vibration_rate * 0.02
        mean_rate += trend_adjustment
        std_rate += trend_adjustment * 0.5
    

    return {
      "healthIndex": round(health_index, 2),
      "meanRate": round(mean_rate, 4),
      "stdRate": round(std_rate, 4)
    }


def calculate_trend(values: List[float]) -> float:
    """Linear trend slope calculation (least squares)"""
    if len(values) < 2:
        return 0.0

    n = len(values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    num = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0





NUM_ITER = 10000
RISK_PERCENTILE = 0.9
FAILURE_THRESHOLD = 1.0


def gaussian_random() -> float:
    """Box-Muller Transform for standard normal values."""
    u = random.random()
    v = random.random()
    return math.sqrt(-2.0 * math.log(u)) * math.cos(2.0 * math.pi * v)


def simulate_time_to_failure(initial_health: float, mean_rate: float, std_rate: float) -> float:
    """Simulates time until failure using stochastic degradation."""
    health = initial_health
    t = 0
    dt = 1
    while health > FAILURE_THRESHOLD:
        rate = mean_rate + std_rate * gaussian_random()
        health -= rate * dt
        t += dt
        if t > 3650:
            break
    return t


def predict_maintenance(structures_data: Dict[str, float]) -> Dict[str, Any]:
    """
    Predict maintenance dates for a list of structures using Monte Carlo simulation.

    Parameters
    ----------
    structures_data : Dict[str, float]
        
        - "healthIndex": float
        - "meanRate": float
        - "stdRate": float

    Returns
    -------
    Dict[str, Any]
        {
            "success": True,
            "prediction": 
                {
                    "predictedNextMaintenance": datetime.datetime,
                    "simulation": {
                        "percentile": float,
                        "daysToMaintain": float
                    }
                }
            
        }
    """
    now = datetime.datetime.utcnow()
    # predictions = []

# for entry in structures_data:
    health_index = structures_data.get("healthIndex")
    mean_rate = structures_data.get("meanRate")
    std_rate = structures_data.get("stdRate")

    samples = [
        simulate_time_to_failure(health_index, mean_rate, std_rate)
        for _ in range(NUM_ITER)
    ]
    samples.sort()
    idx = int(RISK_PERCENTILE * NUM_ITER)
    days_to_maintain = samples[idx]
    maintain_date = now + datetime.timedelta(days=round(days_to_maintain))

    return{
        "predictedNextMaintenance": maintain_date,
        "simulation": {
            "percentile": RISK_PERCENTILE,
            "daysToMaintain": days_to_maintain
        }
    }



def prediction_task():
    try:
        with next(get_db()) as db:
            #get historical and current data
            print("retrieving data")
            data = get_historial_data(db)
            last = data.pop()
            current_data = {
                    "temperature": str(last.temperature),
                    "vibration": str(last.vibration),
                    "pressure": str(last.pressure)
            }
            historical_data = [
                {
                
                    "temperature": str(i.temperature),
                    "vibration": str(i.vibration),
                    "pressure": str(i.pressure)
            }
            for i in data
            ]

            #get the model input
            print("feeding it to the modle")
            model_input_data = translate_sensors_to_model_input(current_data=current_data,historical_data=historical_data)
            print("output 1 :",model_input_data)
            #get prediction
            prediction = predict_maintenance(model_input_data)
            days_to_maintain = int(float(prediction['simulation']['daysToMaintain']))
            print("output 2 : ", prediction)
            print("writing to db")
            new_prediction = Prediction(predicted_maintenance_date=prediction["predictedNextMaintenance"],
                                        days_to_maintain=days_to_maintain,
                                        percentile=prediction["simulation"]["percentile"]
            )

            db.add(new_prediction)
            db.commit()
            db.refresh(new_prediction)


            pass
        pass
    except Exception as e:
        print("Exception occured while running prediction task : ", str(e))

    finally:
        print("Ending prediction task...")

# c_1 =  {
#         "temperature": "32.18",
#         "vibration": "0",
#         "pressure": "1003.76"
#   }
# h_1 =[
#         {"temperature": "28.67", "vibration": "0", "pressure": "1006.44"},
#         {"temperature": "30.51", "vibration": "1", "pressure": "1007.80"},
#         {"temperature": "25.43", "vibration": "0", "pressure": "1002.17"},
#         {"temperature": "29.12", "vibration": "0", "pressure": "1011.66"},
#         {"temperature": "27.38", "vibration": "1", "pressure": "1000.39"},
#         {"temperature": "26.59", "vibration": "0", "pressure": "1005.07"},
#         {"temperature": "24.91", "vibration": "0", "pressure": "1003.94"}
#       ]
# p=[
#     {
#       "healthIndex": 98.0,
#       "meanRate": 0.1324,
#       "stdRate": 0.0434
#     },
#     {
#       "healthIndex": 97.85,
#       "meanRate": 0.1319,
#       "stdRate": 0.042
#     },
#     {
#       "healthIndex": 100.0,
#       "meanRate": 0.1014,
#       "stdRate": 0.0215
#     }
#   ]
# a=translate_sensors_to_model_input(c_1,h_1)
# print("output1 : ",a)

# b=predict_maintenance(a)
# print("output2 : ",b)
