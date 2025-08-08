import os
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv
    for env_path in [".env", "../.env", "../../.env", "../../../.env", Path(__file__).parent.parent.parent / ".env"]:
        if Path(env_path).exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

class Config:
    # Service configuration
    SERVICE_NAME: str = "user-service"
    SERVICE_PORT: int = int(os.getenv("USER_SERVICE_PORT", 8004))
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # JWT configuration (must match auth service)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AWS S3 configuration (optional)
    AWS_ACCESS_KEY_ID: str = os.getenv("ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("SECRET_ACCESS_KEY", "")
    AWS_REGION: str = "ap-northeast-1"
    S3_USER_BUCKET_NAME: str = os.getenv("S3_USER_BUCKET_NAME", "")

    # File upload configuration
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 5242880  # 5MB
    ALLOWED_FILE_TYPES: List[str] = ["jpg", "jpeg", "png", "gif"]

    # Frontend configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

config = Config()

# Helper functions for compatibility
def get_database_url():
    return config.DATABASE_URL

def get_debug_mode():
    return config.DEBUG

def get_service_port():
    return config.SERVICE_PORT

def get_jwt_config():
    return {
        "secret_key": config.JWT_SECRET_KEY,
        "algorithm": config.JWT_ALGORITHM,
        "access_token_expire_minutes": config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    }
