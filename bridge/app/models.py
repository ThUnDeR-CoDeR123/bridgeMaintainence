from datetime import datetime
import json
from sqlalchemy.orm import DeclarativeBase
from typing import List, Optional
from sqlalchemy import (
    String, Integer, Boolean, DateTime, ForeignKey, func, Text,Float
)
from sqlalchemy.orm import ( Mapped, mapped_column, relationship)
import enum

# -----------------------------------------------
# Base with to_dict and to_json
# -----------------------------------------------
class Base(DeclarativeBase):
    def to_dict(self, seen=None):
        if seen is None:
            seen = set()
        if id(self) in seen:
            return {}
        seen.add(id(self))

        data = {}
        for column in self.__table__.columns:
            val = getattr(self, column.name)
            if isinstance(val, datetime):
                data[column.name] = val.isoformat()
            else:
                data[column.name] = val

        for rel_name in self.__mapper__.relationships.keys():
            related_obj = getattr(self, rel_name)
            if related_obj is not None:
                if isinstance(related_obj, list):
                    data[rel_name] = [item.to_dict(seen=seen) for item in related_obj]
                else:
                    data[rel_name] = related_obj.to_dict(seen=seen)

        return data

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)

class HistorialData(Base):
    __tablename__ = 'historial_data'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Optional temperature field
    humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Optional humidity field
    pressure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Optional pressure field
    vibration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Optional vibration field

    def __repr__(self):
        return f"<HistorialData(id={self.id}, timestamp={self.timestamp}, source={self.source})>"
    

class RiskLevel(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"



class BridgeHealthAnalysis(Base):
    __tablename__ = "bridge_health_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Current Health Metrics
    health_index: Mapped[float] = mapped_column(Float, nullable=False)
    mean_rate: Mapped[float] = mapped_column(Float, nullable=False)
    std_rate: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Time to Failure Predictions
    mean_time_to_failure: Mapped[Optional[float]] = mapped_column(Float)  # in days
    conservative_maintenance: Mapped[Optional[float]] = mapped_column(Float)  # in days
    balanced_maintenance: Mapped[Optional[float]] = mapped_column(Float)  # in days
    
    # Risk Assessment
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    
    
    def __repr__(self):
        return f"<BridgeHealthAnalysis(id={self.id}, health_index={self.health_index}, risk_level={self.risk_level})>"
    

#output2 :  {'predictedNextMaintenance': '2027-08-27 08:22:43.812693', 'simulation': {'percentile': 0.9, 'daysToMaintain': 805}}

class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Maintenance prediction fields
    predicted_maintenance_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    days_to_maintain: Mapped[int] = mapped_column(Integer, nullable=False)
    percentile: Mapped[float] = mapped_column(Float, nullable=False, default=0.9)

    def __repr__(self):
        return f"<Prediction(id={self.id}, days_to_maintain={self.days_to_maintain}, predicted_date={self.predicted_maintenance_date})>"