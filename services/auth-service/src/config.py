"""
Standalone configuration for Auth Service
Self-contained config that doesn't depend on external modules
"""
import os
from pathlib import Path
from typing import List


def load_env_file():
    """Load environment variables from .env files"""
    try:
        # Try to load python-dotenv if available
        from dotenv import load_dotenv
        
        # Try different locations for .env file
        env_paths = [
            ".env.local",
            ".env",
            "../.env.local", 
            "../.env",
            "../../.env.local",
            "../../.env",
            "../../../.env",
            "/tmp/.env"  # For Lambda
        ]
        
        for env_path in env_paths:
            if Path(env_path).exists():
                load_dotenv(env_path)
                print(f"Auth Service: Loaded environment from: {env_path}")
                return True
        
        print("Auth Service: No .env file found, using environment variables")
        return False
    except ImportError:
        print("Auth Service: python-dotenv not installed, using environment variables")
        return False


# Auto-load environment
load_env_file()


class AuthConfig:
    """Self-contained configuration for Auth Service"""
    
    # Service Info
    SERVICE_NAME: str = "auth-service"
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database - Priority: .env.local > .env > default
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:1210@localhost:5432/pathlight"
    )
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", 
        "your-super-secret-jwt-key-here-change-in-production-please"
    )
    JWT_REFRESH_SECRET_KEY: str = os.getenv(
        "JWT_REFRESH_SECRET_KEY", 
        "your-super-secret-refresh-key-here-change-in-production-please"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@pathlight.com")
    
    # Email Verification
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "10"))
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Admin
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Other Services (for microservice communication)
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
    COURSE_SERVICE_URL: str = os.getenv("COURSE_SERVICE_URL", "http://localhost:8003")
    QUIZ_SERVICE_URL: str = os.getenv("QUIZ_SERVICE_URL", "http://localhost:8004")
    
    # App Info
    APP_NAME: str = os.getenv("APP_NAME", "PathLight")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")


# Create global config instance
config = AuthConfig()


def get_database_url():
    """Get database URL"""
    return config.DATABASE_URL


def get_debug_mode():
    """Get debug mode"""
    return config.DEBUG


def get_jwt_config():
    """Get JWT configuration"""
    return {
        "secret_key": config.JWT_SECRET_KEY,
        "refresh_secret_key": config.JWT_REFRESH_SECRET_KEY,
        "algorithm": config.JWT_ALGORITHM,
        "access_token_expire_minutes": config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_days": config.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    }


def get_service_port():
    """Get service port"""
    return config.SERVICE_PORT


def get_cors_config():
    """Get CORS configuration"""
    return {
        "allow_origins": config.ALLOWED_ORIGINS,
        "allow_methods": config.ALLOWED_METHODS,
        "allow_headers": config.ALLOWED_HEADERS,
        "allow_credentials": True
    }


def get_email_config():
    """Get email configuration"""
    return {
        "smtp_server": config.SMTP_SERVER,
        "smtp_port": config.SMTP_PORT,
        "smtp_username": config.SMTP_USERNAME,
        "smtp_password": config.SMTP_PASSWORD,
        "from_email": config.FROM_EMAIL
    }


# Print loaded configuration on import (debug mode only)
if config.DEBUG:
    print("=== Auth Service Configuration ===")
    print(f"SERVICE_NAME: {config.SERVICE_NAME}")
    print(f"SERVICE_PORT: {config.SERVICE_PORT}")
    print(f"DATABASE_URL: {config.DATABASE_URL}")
    print(f"DEBUG: {config.DEBUG}")
    print(f"ENVIRONMENT: {config.ENVIRONMENT}")
    print(f"FRONTEND_URL: {config.FRONTEND_URL}")
    print(f"JWT_ALGORITHM: {config.JWT_ALGORITHM}")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES}")
