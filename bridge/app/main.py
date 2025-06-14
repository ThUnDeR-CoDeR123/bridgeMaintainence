from fastapi import FastAPI, Depends, HTTPException, status,Request
from sqlalchemy.orm import Session
from app.database import  engine
from app.models import Base,Prediction
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from fastapi.responses import JSONResponse
from app.crud import get_historial_data, create_historial_data, delete_historial_data, get_historial_data_by_id
from app.database import get_db
from contextlib import asynccontextmanager
from sqlalchemy import desc
import threading
import schedule
import time
from app.core import prediction_task
import struct

# from pathlib import Path
Base.metadata.create_all(bind=engine)

def startSchedulerInBackground():
    schedulerThread = threading.Thread(target=runScheduler, daemon=True)
    schedulerThread.start()
    # Schedule the health monitoring task every 60 seconds
    schedule.every(60).seconds.do(update_bridge_health)

def runScheduler():
    while True:
        print("Health monitoring scheduler running...")
        schedule.run_pending()
        time.sleep(10)

def stop_scheduler():
    schedule.clear()

def update_bridge_health():
    try:
        print("Updating bridge health analysis...")
        if read_flag()==True:
            print("flag set to true calling prediction task...")
            prediction_task()
        else:
            print("flag set to false skipping prediction task ...")
    except Exception as e:
        print(f"Error during health update: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and start scheduler
    Base.metadata.create_all(bind=engine)
    startSchedulerInBackground()
    yield
    # Shutdown: Stop scheduler
    stop_scheduler()

app = FastAPI(
    lifespan=lifespan
)

FLAG =  "flag.bin"
def read_flag() -> bool:
    """
    Read boolean flag from binary file
    
    Returns:
        bool: The flag value (False if file doesn't exist)
    """
    try:
        with open(FLAG, "rb") as f:
            return struct.unpack('?', f.read(1))[0]  # '?' for boolean, read 1 byte
    except FileNotFoundError:
        return False  # Return False as default
    
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def home():
    return {"hello": "world"}


@app.get("/set-flag/{flag_value}", response_model=dict)
async def write_flag(flag_value: int) -> dict:
    """
    Write boolean flag to binary file
    
    Args:
        flag_value (int): 1 for True, 0 for False
    
    Returns:
        dict: Operation status and current flag value
    """
    try:
        # Validate input
        if flag_value not in [0, 1]:
            raise HTTPException(
                status_code=400,
                detail="Flag value must be 0 or 1"
            )
        
        # Convert to boolean
        bool_value = True if flag_value == 1 else False
        
        # Write to file
        with open(FLAG, "wb") as f:
            f.write(struct.pack('?', bool_value))
            
        return {
            "success": True,
            "flag_value": bool_value,
            "message": f"Flag set to {bool_value}"
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write flag: {str(e)}"
        )


#crud routes

@app.get('/historial_data', response_model=list)
def read_historial_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db = next(get_db())
    data = get_historial_data(db, skip=skip, limit=limit)
    return data

@app.get('/historial_data/{id}', response_model=dict)
def read_historial_data_by_id(id: int, db: Session = Depends(get_db)):
    db = next(get_db())
    data = get_historial_data_by_id(db, id=id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data not found")
    return data

@app.post('/historial_data', response_model=dict)
def create_historial_data_endpoint(
    temperature: float = None, 
    humidity: float = None, 
    pressure: float = None, 
    vibration: float = None, 
    db: Session = Depends(get_db)
):
    data = create_historial_data(db, temperature=temperature, humidity=humidity, pressure=pressure, vibration=vibration)
    return data.to_dict()



@app.get("/prediction")
def get_prediction(db: Session = Depends(get_db)):
    return db.query(Prediction).order_by(desc(Prediction.created_at)).first()
