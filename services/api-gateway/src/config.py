import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load global .env from project root
root_dir = Path(__file__).parent.parent.parent.parent
load_dotenv(root_dir / ".env")

class Config:
    # =============================================================================
    # API GATEWAY CONFIGURATION (Entry Point - cần config đầy đủ)
    # =============================================================================
    
    # API Gateway Settings
    GATEWAY_HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
    GATEWAY_PORT = int(os.getenv("API_GATEWAY_PORT", 8000))
    
    # Client CORS Settings (chỉ cho phép frontend)
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    ALLOWED_METHODS = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    ALLOWED_HEADERS = os.getenv("ALLOWED_HEADERS", "*").split(",")
    
    # Service Discovery - API Gateway cần biết tất cả services
    SERVICES = {
        "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
        "user": os.getenv("USER_SERVICE_URL", "http://user-service:8002"), 
        "course": os.getenv("COURSE_SERVICE_URL", "http://course-service:8003"),
        "quiz": os.getenv("QUIZ_SERVICE_URL", "http://quiz-service:8004"),
    }
    
    # Authentication (để verify JWT từ clients)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    
    # Application Config
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))
    
    # Timeout Settings
    SERVICE_TIMEOUT = float(os.getenv("SERVICE_TIMEOUT", 30.0))
    HEALTH_CHECK_TIMEOUT = float(os.getenv("HEALTH_CHECK_TIMEOUT", 5.0))

# Route configurations
class Routes:
    # Public endpoints (không cần authentication)
    PUBLIC_ENDPOINTS = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register", 
        "/api/auth/refresh",
        "/api/auth/forgot-password",
    }
    
    # Protected endpoints (cần authentication)
    PROTECTED_ENDPOINTS = {
        "/api/user/",
        "/api/course/",
        "/api/quiz/",
    }
    
    # Admin endpoints (cần admin role)
    ADMIN_ENDPOINTS = {
        "/api/admin/",
        "/api/auth/reset-password",
    }
    
    # Protected endpoints (authentication required)
    PROTECTED_ENDPOINTS = {
        "/api/user/",
        "/api/course/",
        "/api/lesson/", 
        "/api/quiz/",
        "/api/test/",
        "/api/auth/profile",
        "/api/auth/logout",
    }
    
    # Admin only endpoints
    ADMIN_ENDPOINTS = {
        "/api/admin/",
        "/api/user/admin/",
        "/api/course/admin/",
    }

config = Config()
routes = Routes()
