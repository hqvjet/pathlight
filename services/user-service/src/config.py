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
    BASE_URL: str = "http://localhost"
    SERVICE_PORT: int = 8002
    COURSE_SERVICE_PORT: int = 8003
    QUIZ_SERVICE_PORT: int = 8004
    USER_SERVICE_URL: str =f"{BASE_URL}:{SERVICE_PORT}"
    COURSE_SERVICE_URL: str =f"{BASE_URL}:{COURSE_SERVICE_PORT}"
    QUIZ_SERVICE_URL: str =f"{BASE_URL}:{QUIZ_SERVICE_PORT}"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    AWS_ACCESS_KEY_ID: str = os.getenv("ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("SECRET_ACCESS_KEY", "")
    AWS_REGION: str = "ap-northeast-1"
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 5242880  # 5MB
    ALLOWED_FILE_TYPES: List[str] = ["jpg", "jpeg", "png", "gif"]

    FRONTEND_URL: str = "http://localhost:3000"

config = Config()
