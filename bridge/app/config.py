from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database and service URLs
    database_url: str 
    class Config:
        env_file = ".env"


settings = Settings()
