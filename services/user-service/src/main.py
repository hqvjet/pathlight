from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import jwt
import os
from datetime import datetime
import logging

# Configuration from environment
USER_SERVICE_PORT = int(os.getenv("USER_SERVICE_PORT", "8002"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pathlight-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# CORS - CHỈ CHO PHÉP API GATEWAY
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
ALLOWED_ORIGINS = [
    API_GATEWAY_URL,
    "http://localhost:8000",  # for development
]

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(title="User Service", version="1.0.0")

# CORS - CHỈ CHO PHÉP API GATEWAY
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Chỉ API Gateway
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic models
class UserProfile(BaseModel):
    email: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UpdateProfileRequest(BaseModel):
    given_name: Optional[str] = None
    family_name: Optional[str] = None

class EnrollmentRequest(BaseModel):
    course_id: str

class CourseProgress(BaseModel):
    course_id: str
    course_title: str
    progress_percentage: float
    last_accessed: Optional[datetime] = None

class UserStats(BaseModel):
    total_courses: int
    completed_courses: int
    total_hours: float

# Mock users database (in real app, use proper database)
mock_users = {
    "user123": {
        "email": "john@example.com",
        "given_name": "John",
        "family_name": "Doe",
        "avatar_url": "https://example.com/avatar.jpg"
    }
}

def verify_token(request: Request):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except:
        return None

@app.get("/")
async def root():
    return {"message": "User Service đang chạy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "user-service"}

@app.get("/api/v1/profile")
async def get_profile(request: Request):
    """Lấy thông tin profile người dùng"""
    user_id = verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    
    # Mock response - in real app, query database
    user_data = mock_users.get(user_id, {
        "email": "user@example.com",
        "given_name": "User",
        "family_name": "Name",
        "avatar_url": None
    })
    
    return {"status": 200, "data": user_data}

@app.put("/api/v1/profile")
async def update_profile(request: Request, profile_data: UpdateProfileRequest):
    """Cập nhật thông tin profile"""
    user_id = verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    
    # Mock update - in real app, update database
    logger.info(f"Updating profile for user {user_id}: {profile_data}")
    
    return {"status": 200, "message": "Profile updated successfully"}

@app.get("/api/v1/courses/enrolled")
async def get_enrolled_courses(request: Request):
    """Lấy danh sách khóa học đã đăng ký"""
    user_id = verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    
    # Mock data - in real app, query database
    enrolled_courses = [
        {
            "course_id": "course1",
            "course_title": "Python Cơ Bản",
            "progress_percentage": 75.5,
            "last_accessed": "2025-06-20T10:30:00"
        },
        {
            "course_id": "course2", 
            "course_title": "Web Development",
            "progress_percentage": 42.0,
            "last_accessed": "2025-06-22T14:15:00"
        }
    ]
    
    return {"status": 200, "data": enrolled_courses}

@app.post("/api/v1/courses/enroll")
async def enroll_course(request: Request, enrollment: EnrollmentRequest):
    """Đăng ký khóa học"""
    user_id = verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    
    # Mock enrollment - in real app, add to database
    logger.info(f"User {user_id} enrolling in course {enrollment.course_id}")
    
    return {"status": 200, "message": "Enrolled successfully"}

@app.delete("/api/v1/courses/{course_id}/unenroll")
async def unenroll_course(request: Request, course_id: str):
    """Hủy đăng ký khóa học"""
    user_id = verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    
    # Mock unenrollment - in real app, remove from database
    logger.info(f"User {user_id} unenrolling from course {course_id}")
    
    return {"status": 200, "message": "Unenrolled successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=USER_SERVICE_PORT)
