from app.models import HistorialData
from sqlalchemy.orm import Session
from sqlalchemy import desc,func,MetaData,text
from typing import List, Optional

# crud functions for HistorialData
def get_historial_data(db: Session, skip: int = 0, limit: int = 100) -> List[HistorialData]:
    return db.query(HistorialData).order_by(desc(HistorialData.timestamp)).offset(skip).limit(limit).all()

def get_historial_data_by_id(db: Session, id: int) -> Optional[HistorialData]:
    return db.query(HistorialData).filter(HistorialData.id == id).first()


def create_historial_data(db: Session, temperature: Optional[float] = None, 
                          humidity: Optional[float] = None, 
                          pressure: Optional[float] = None, 
                          vibration: Optional[float] = None) -> HistorialData:
    new_data = HistorialData(
        temperature=temperature,
        humidity=humidity,
        pressure=pressure,
        vibration=vibration
    )
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data

def delete_historial_data(db: Session, id: int) -> Optional[HistorialData]:
    data = db.query(HistorialData).filter(HistorialData.id == id).first()
    if data:
        db.delete(data)
        db.commit()
        return data
    return None
