import os
from typing import Dict, List

class Config:
    # API Gateway Settings
    GATEWAY_HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
    GATEWAY_PORT = int(os.getenv("API_GATEWAY_PORT", 8000))
    
    # CORS Settings
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    ALLOWED_METHODS = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
    ALLOWED_HEADERS = os.getenv("ALLOWED_HEADERS", "*").split(",")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))
    
    # Service Discovery
    SERVICES = {
        "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
        "user": os.getenv("USER_SERVICE_URL", "http://localhost:8002"), 
        "course": os.getenv("COURSE_SERVICE_URL", "http://localhost:8003"),
        "quiz": os.getenv("QUIZ_SERVICE_URL", "http://localhost:8004"),
        "test": os.getenv("TEST_SERVICE_URL", "http://localhost:8005"),
        "lesson": os.getenv("LESSON_SERVICE_URL", "http://localhost:8006"),
    }
    
    # Authentication
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Timeout Settings
    SERVICE_TIMEOUT = float(os.getenv("SERVICE_TIMEOUT", 30.0))
    HEALTH_CHECK_TIMEOUT = float(os.getenv("HEALTH_CHECK_TIMEOUT", 5.0))

# Route configurations
class Routes:
    # Public endpoints (no authentication required)
    PUBLIC_ENDPOINTS = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/refresh",
        "/api/auth/forgot-password",
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
