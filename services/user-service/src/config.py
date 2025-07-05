"""
Configuration for Pathlight User Service
Standalone configuration without API Gateway dependencies
"""
import os
from pathlib import Path
from typing import List


def load_env():
    """Load environment variables from various locations"""
    try:
        from dotenv import load_dotenv
        # Try different locations for .env file
        env_paths = [
            ".env",
            "../.env", 
            "../../.env",
            "../../../.env",
            Path(__file__).parent.parent.parent / ".env"
        ]
        
        for env_path in env_paths:
            if Path(env_path).exists():
                load_dotenv(env_path)
                return True
        return False
    except ImportError:
        return False


# Auto-load environment variables
load_env()


class UserServiceConfig:
    """Configuration for Pathlight User Service"""
    
    # Service Configuration
    SERVICE_NAME: str = "pathlight-user-service"
    SERVICE_PORT: int = int(os.getenv("USER_SERVICE_PORT", "8002"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/pathlight"
    )
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", 
        "pathlight-super-secret-key-2025-standalone"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # File Upload Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "5242880"))  # 5MB
    ALLOWED_FILE_TYPES: List[str] = os.getenv("ALLOWED_FILE_TYPES", "jpg,jpeg,png,gif").split(",")
    
    # Frontend Configuration (for CORS)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Email Configuration (for future features)
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")


# Create global config instance
config = UserServiceConfig()


# Helper functions for backward compatibility
def get_database_url():
    """Get database URL"""
    return config.DATABASE_URL


def get_debug_mode():
    """Get debug mode setting"""
    return config.DEBUG


def get_service_port():
    """Get service port"""
    return config.SERVICE_PORT


def get_jwt_secret():
    """Get JWT secret key"""
    return config.JWT_SECRET_KEY
