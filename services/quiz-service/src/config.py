"""
Configuration for Quiz Service
All configurations needed for quiz service to run independently
"""
import os
from pathlib import Path
from typing import List


def load_env():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        # Try different locations for .env file
        env_paths = [
            ".env",
            "../.env", 
            "../../.env",
            "../../../.env",
            "/tmp/.env"  # For Lambda
        ]
        
        for env_path in env_paths:
            if Path(env_path).exists():
                load_dotenv(env_path)
                return True
        return False
    except ImportError:
        return False


# Auto-load environment
load_env()


class QuizConfig:
    """Configuration for Quiz Service"""
    
    # Service
    SERVICE_NAME: str = "quiz-service"
    SERVICE_PORT: int = 8004
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]


# Create global config instance
config = QuizConfig()


# Helper functions for backward compatibility
def get_database_url():
    return config.DATABASE_URL


def get_debug_mode():
    return config.DEBUG


def get_service_port():
    return config.SERVICE_PORT
