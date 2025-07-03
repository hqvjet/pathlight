"""
Configuration for User Service
All configurations needed for user service to run independently
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


class UserConfig:
    """Configuration for User Service"""
    
    # Service
    SERVICE_NAME: str = "user-service"
    SERVICE_PORT: int = int(os.getenv("USER_SERVICE_PORT", "8002"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/pathlight")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    ALLOWED_METHODS: List[str] = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    ALLOWED_HEADERS: List[str] = os.getenv("ALLOWED_HEADERS", "*").split(",")
    
    # API Gateway URL (for CORS)
    API_GATEWAY_URL: str = os.getenv("API_GATEWAY_URL", "http://localhost:8000")


# Create global config instance
config = UserConfig()


# Helper functions for backward compatibility
def get_database_url():
    return config.DATABASE_URL


def get_debug_mode():
    return config.DEBUG


def get_service_port():
    return config.SERVICE_PORT
