from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Real Estate Analysis API"
    database_url: str = "postgresql://username:password@localhost:5432/real_estate"
    allowed_origins: list = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()
