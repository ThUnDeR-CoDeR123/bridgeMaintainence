from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
from tenacity import retry, stop_after_attempt, wait_fixed

SQLALCHEMY_DATABASE_URL = settings.database_url

# Retry mechanism for database connection
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))  # Retry 5 times, wait 2 seconds between retries
def create_engine_with_retry():
    return create_engine(SQLALCHEMY_DATABASE_URL)

engine = create_engine_with_retry()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()