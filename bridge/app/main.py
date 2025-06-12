from fastapi import FastAPI, Depends, HTTPException, status,Request
from sqlalchemy.orm import Session
from app.database import  engine
from app.models import Base
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from fastapi.responses import JSONResponse
from app.crud import get_historial_data, create_historial_data, delete_historial_data, get_historial_data_by_id
from app.database import get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()


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



