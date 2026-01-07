from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/agenttrace"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Authentication
    JWT_SECRET: str = "your-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 3600

    # Logging
    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
