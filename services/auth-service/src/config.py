"""
Shared configuration for Auth Service
All configurations needed for auth service to run independently
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


class AuthConfig:
    """Configuration for Auth Service"""
    
    # Service
    SERVICE_NAME: str = "auth-service"
    SERVICE_PORT: int = int(os.getenv("AUTH_SERVICE_PORT", "8001"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/pathlight")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "pathlight-refresh-secret-key-2025")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    ALLOWED_METHODS: List[str] = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    ALLOWED_HEADERS: List[str] = os.getenv("ALLOWED_HEADERS", "*").split(",")
    
    # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@pathlight.com")
    
    # Admin
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Email verification
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "10"))


# Create global config instance
config = AuthConfig()


# Helper functions for backward compatibility
def get_database_url():
    return config.DATABASE_URL


def get_debug_mode():
    return config.DEBUG


def get_jwt_config():
    return {
        "secret_key": config.JWT_SECRET_KEY,
        "refresh_secret_key": config.JWT_REFRESH_SECRET_KEY,
        "algorithm": config.JWT_ALGORITHM,
        "access_token_expire_minutes": config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_days": config.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    }


def get_service_port():
    return config.SERVICE_PORT
