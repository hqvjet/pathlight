import os
from pathlib import Path
from dotenv import load_dotenv

# Load global .env from project root
root_dir = Path(__file__).parent.parent.parent.parent
load_dotenv(root_dir / ".env")

# =============================================================================
# USER SERVICE SPECIFIC CONFIG (chỉ cần config cho service này)
# =============================================================================

# Database Configuration (shared với các services khác)
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Compose Database URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Service Port (chỉ service này cần)
USER_SERVICE_PORT = int(os.getenv("USER_SERVICE_PORT", "8002"))

# Application Config
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# JWT Config (để verify tokens từ API Gateway)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# CORS - CHỈ CHO PHÉP API GATEWAY
# Services chỉ nhận requests từ API Gateway, không từ client trực tiếp  
ALLOWED_ORIGINS = [
    os.getenv("API_GATEWAY_URL", "http://api-gateway:8000"),
    "http://localhost:8000",  # cho development
]
