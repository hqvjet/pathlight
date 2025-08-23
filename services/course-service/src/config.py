"""
Configuration for Course Service
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment from common paths
_dotenv_override = (
    os.getenv("AWS_LAMBDA_FUNCTION_NAME") is None
    and os.getenv("DOTENV_OVERRIDE", "true").lower() == "true"
)
for env_path in [".env", "../.env", "../../.env", "../../../.env", "/tmp/.env"]:
    if Path(env_path).exists():
        load_dotenv(env_path, override=_dotenv_override)
        break

class CourseConfig:
    SERVICE_PORT: int = int(os.getenv("COURSE_SERVICE_PORT", 8002))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]

    # AWS S3
    ACCESS_KEY_ID: str = os.getenv("ACCESS_KEY_ID", "")
    SECRET_ACCESS_KEY: str = os.getenv("SECRET_ACCESS_KEY", "")
    REGION: str = os.getenv("REGION", "ap-northeast-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")

    AGENTIC_SERVICE_ENDPOINT: str = os.getenv("AGENTIC_SERVICE_ENDPOINT", "https://zlly4nvqqa3e7hag574nsvcgiy0tlekb.lambda-url.ap-northeast-1.on.aws/agentic/vectorize")

config = CourseConfig()

def get_database_url(): 
    return config.DATABASE_URL 

def get_debug_mode(): 
    return config.DEBUG 

def get_service_port(): 
    return config.SERVICE_PORT