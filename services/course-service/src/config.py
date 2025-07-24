"""
Configuration for Course Service
All configurations needed for course service to run independently
"""
import os
from pathlib import Path
from typing import List


def load_env():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        env_paths = [
            ".env",
            "../.env", 
            "../../.env",
            "../../../.env",
            "/tmp/.env" 
        ]
        
        for env_path in env_paths:
            if Path(env_path).exists():
                load_dotenv(env_path)
                return True
        return False
    except ImportError:
        return False


load_env()

class CourseConfig:
    """Configuration for Course Service"""
    SERVICE_NAME: str = "course-service"
    SERVICE_PORT: int = 8003
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]

config = CourseConfig()

def get_database_url():
    return config.DATABASE_URL

def get_debug_mode():
    return config.DEBUG

def get_service_port():
    return config.SERVICE_PORT
