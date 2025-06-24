"""
Shared configuration module for PathLight services
Loads environment variables with sensible defaults
"""
import os
from pathlib import Path
from typing import List, Optional


def load_env_from_root():
    """Load environment variables from root .env file"""
    try:
        from dotenv import load_dotenv
        # Find .env file in project root
        current_file = Path(__file__)
        # Navigate from libs/common-utils-py/utils/ -> pathlight/
        root_dir = current_file.parent.parent.parent.parent
        env_path = root_dir / ".env"
        
        if env_path.exists():
            load_dotenv(env_path)
            return True
        else:
            print(f"Warning: .env file not found at {env_path}")
            return False
    except ImportError:
        print("Warning: python-dotenv not installed. Using system environment variables only.")
        return False


class Config:
    """Base configuration class with common settings"""
    
    def __init__(self):
        # Ensure .env is loaded
        load_env_from_root()
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "PathLight")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/pathlight")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "pathlight")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    
    # Service Ports
    API_GATEWAY_PORT: int = int(os.getenv("API_GATEWAY_PORT", "8000"))
    AUTH_SERVICE_PORT: int = int(os.getenv("AUTH_SERVICE_PORT", "8001"))
    USER_SERVICE_PORT: int = int(os.getenv("USER_SERVICE_PORT", "8002"))
    COURSE_SERVICE_PORT: int = int(os.getenv("COURSE_SERVICE_PORT", "8003"))
    QUIZ_SERVICE_PORT: int = int(os.getenv("QUIZ_SERVICE_PORT", "8004"))
    
    # Service URLs
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8002")
    COURSE_SERVICE_URL: str = os.getenv("COURSE_SERVICE_URL", "http://course-service:8003")
    QUIZ_SERVICE_URL: str = os.getenv("QUIZ_SERVICE_URL", "http://quiz-service:8004")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "change-this-refresh-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
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
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL for SQLAlchemy"""
        return cls.DATABASE_URL
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.ENVIRONMENT.lower() == "development"
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.ENVIRONMENT.lower() == "production"


# Compatibility functions for legacy code
def get_database_url() -> str:
    """Get database URL from environment"""
    load_env_from_root()
    return os.getenv("DATABASE_URL", "postgresql://postgres:1210@localhost:5433/pathlight")

def get_service_port(service_name: str) -> int:
    """Get service port from environment"""
    load_env_from_root()
    port_map = {
        "auth": int(os.getenv("AUTH_SERVICE_PORT", "8001")),
        "user": int(os.getenv("USER_SERVICE_PORT", "8002")),
        "course": int(os.getenv("COURSE_SERVICE_PORT", "8003")),
        "quiz": int(os.getenv("QUIZ_SERVICE_PORT", "8004")),
        "gateway": int(os.getenv("API_GATEWAY_PORT", "8000")),
    }
    return port_map.get(service_name, 8000)

def get_service_url(service_name: str) -> str:
    """Get service URL from environment"""
    load_env_from_root()
    url_map = {
        "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
        "user": os.getenv("USER_SERVICE_URL", "http://user-service:8002"),
        "course": os.getenv("COURSE_SERVICE_URL", "http://course-service:8003"),
        "quiz": os.getenv("QUIZ_SERVICE_URL", "http://quiz-service:8004"),
    }
    return url_map.get(service_name, "http://localhost:8000")


# Create a global config instance
config = Config()

# Legacy compatibility functions for existing services
def get_database_url() -> str:
    """Get database URL from environment - Legacy compatibility function"""
    return config.get_database_url()

def get_debug_mode() -> bool:
    """Get debug mode setting - Legacy compatibility function"""
    return config.DEBUG

def get_debug_mode() -> bool:
    """Get debug mode setting - Legacy compatibility function"""
    return config.DEBUG

def get_service_port(service_name: str) -> int:
    """Get service port from environment - Legacy compatibility function"""
    port_map = {
        "auth": config.AUTH_SERVICE_PORT,
        "user": config.USER_SERVICE_PORT,
        "course": config.COURSE_SERVICE_PORT,
        "quiz": config.QUIZ_SERVICE_PORT,
        "gateway": config.API_GATEWAY_PORT,
    }
    return port_map.get(service_name, 8000)

def get_service_url(service_name: str) -> str:
    """Get service URL from environment - Legacy compatibility function"""
    url_map = {
        "auth": config.AUTH_SERVICE_URL,
        "user": config.USER_SERVICE_URL,
        "course": config.COURSE_SERVICE_URL,
        "quiz": config.QUIZ_SERVICE_URL,
    }
    return url_map.get(service_name, "http://localhost:8000")

def get_jwt_config() -> dict:
    """Get JWT configuration - Legacy compatibility function"""
    return {
        "secret_key": config.JWT_SECRET_KEY,
        "refresh_secret_key": config.JWT_REFRESH_SECRET_KEY,
        "algorithm": config.JWT_ALGORITHM,
        "access_token_expire_minutes": config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_days": config.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    }

def is_development() -> bool:
    """Check if running in development mode - Legacy compatibility function"""
    return config.is_development()

def is_debug() -> bool:
    """Check if debug mode is enabled - Legacy compatibility function"""
    return config.DEBUG
