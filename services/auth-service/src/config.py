"""
Standalone configuration for Auth Service
"""
import os
from pathlib import Path
from typing import List


def load_env_file():
    """Load environment variables from .env files"""
    try:
        from dotenv import load_dotenv
        
        env_paths = [
            ".env.local",
            ".env",
            "../.env.local", 
            "../.env",
            "../../.env.local",
            "../../.env",
            "../../../.env",
            "/tmp/.env" 
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

load_env_file()

class AuthConfig:
    """Self-contained configuration for Auth Service"""
    SERVICE_NAME: str = "auth-service"
    SERVICE_PORT: int = int(os.getenv("AUTH_SERVICE_PORT", 8001))
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = "noreply@pathlight.com"

    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 10

    FRONTEND_URL: str = "http://localhost:3000"

    ADMIN_USERNAME: str = ""
    ADMIN_PASSWORD: str = ""

    ENDPOINT: str = os.getenv("ENDPOINT", "http://localhost")
    AUTH_SERVICE_PORT: int = int(os.getenv("AUTH_SERVICE_PORT", 8001))
    USER_SERVICE_PORT: int = int(os.getenv("USER_SERVICE_PORT", 8002))
    COURSE_SERVICE_PORT: int = int(os.getenv("COURSE_SERVICE_PORT", 8003))
    QUIZ_SERVICE_PORT: int = int(os.getenv("QUIZ_SERVICE_PORT", 8004))

    AUTH_SERVICE_ENDPOINT: str = os.getenv("AUTH_SERVICE_ENDPOINT", f"{ENDPOINT}:{AUTH_SERVICE_PORT}")
    USER_SERVICE_ENDPOINT: str = os.getenv("USER_SERVICE_ENDPOINT", f"{ENDPOINT}:{USER_SERVICE_PORT}")
    COURSE_SERVICE_ENDPOINT: str = os.getenv("COURSE_SERVICE_ENDPOINT", f"{ENDPOINT}:{COURSE_SERVICE_PORT}")
    QUIZ_SERVICE_ENDPOINT: str = os.getenv("QUIZ_SERVICE_ENDPOINT", f"{ENDPOINT}:{QUIZ_SERVICE_PORT}")

    APP_NAME: str = "PathLight"
    ENVIRONMENT: str = "development"

config = AuthConfig()

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

def get_cors_config():
    return {
        "allow_origins": config.ALLOWED_ORIGINS,
        "allow_methods": config.ALLOWED_METHODS,
        "allow_headers": config.ALLOWED_HEADERS,
        "allow_credentials": True
    }

def get_email_config():
    return {
        "smtp_server": config.SMTP_SERVER,
        "smtp_port": config.SMTP_PORT,
        "smtp_username": config.SMTP_USERNAME,
        "smtp_password": config.SMTP_PASSWORD,
        "from_email": config.FROM_EMAIL
    }

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