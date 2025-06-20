"""
Centralized configuration management for PathLight services.
Loads environment variables from root .env file.
"""
import os
from pathlib import Path
from typing import Optional

def load_env_from_root():
    """Load environment variables from root .env file"""
    try:
        from dotenv import load_dotenv
        # Tìm file .env ở root project
        current_file = Path(__file__)
        # Đi lên từ libs/common-utils-py/utils/ -> pathlight/
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
        "test": int(os.getenv("TEST_SERVICE_PORT", "8005")),
        "gateway": int(os.getenv("API_GATEWAY_PORT", "8000")),
    }
    return port_map.get(service_name, 8000)

def get_service_url(service_name: str) -> str:
    """Get service URL from environment"""
    load_env_from_root()
    url_map = {
        "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
        "user": os.getenv("USER_SERVICE_URL", "http://localhost:8002"),
        "course": os.getenv("COURSE_SERVICE_URL", "http://localhost:8003"),
        "quiz": os.getenv("QUIZ_SERVICE_URL", "http://localhost:8004"),
        "test": os.getenv("TEST_SERVICE_URL", "http://localhost:8005"),
    }
    return url_map.get(service_name, "http://localhost:8000")

def get_jwt_config() -> dict:
    """Get JWT configuration"""
    load_env_from_root()
    return {
        "secret_key": os.getenv("JWT_SECRET_KEY", "pathlight-secret"),
        "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
        "expire_minutes": int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    }

def is_development() -> bool:
    """Check if running in development mode"""
    load_env_from_root()
    return os.getenv("ENVIRONMENT", "development").lower() == "development"

def is_debug() -> bool:
    """Check if debug mode is enabled"""
    load_env_from_root()
    return os.getenv("DEBUG", "false").lower() == "true"
