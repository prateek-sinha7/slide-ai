"""Backend configuration settings."""
import os
from typing import Optional


class Config:
    """Application configuration."""
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_EXPIRATION_HOURS: int = 24
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    # Generation timeouts (seconds)
    GENERATION_TIMEOUT: int = 200
    LLM_TIMEOUT: int = 120
    PPT_TIMEOUT: int = 10
    
    # Validation limits
    MAX_TOPIC_LENGTH: int = 500
    MIN_SLIDE_COUNT: int = 5
    MAX_SLIDE_COUNT: int = 20
    DEFAULT_SLIDE_COUNT: int = 8
    MIN_PASSWORD_LENGTH: int = 8
    
    # File storage
    TEMP_FILE_DIR: str = os.getenv("TEMP_FILE_DIR", "./temp_presentations")
    FILE_EXPIRATION_HOURS: int = 1


config = Config()
