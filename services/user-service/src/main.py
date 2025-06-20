from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import jwt
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="User Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
JWT_ALGORITHM = "HS256"

class UserProfile(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    location: Optional[str] = None
    preferences: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EnrollmentRequest(BaseModel):
    course_id: int

class ProgressUpdate(BaseModel):
    lesson_id: int
    progress: float
    completed: bool

users_db = {}
enrollments_db = {}
progress_db = {}

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
    user_email = verify_token(request)
    if not user_email:
        return {"status": 401, "message": "Unauthorized"}
    
    profile = users_db.get(user_email, {
        "email": user_email,
        "created_at": datetime.utcnow()
    })
    
    return {"status": 200, "profile": profile}

@app.put("/api/v1/profile")
async def update_profile(profile: UserProfile, request: Request):
    user_email = verify_token(request)
    if not user_email:
        return {"status": 401, "message": "Unauthorized"}
    
    profile_data = profile.dict()
    profile_data["email"] = user_email
    profile_data["updated_at"] = datetime.utcnow()
    
    if user_email not in users_db:
        profile_data["created_at"] = datetime.utcnow()
    else:
        profile_data["created_at"] = users_db[user_email].get("created_at", datetime.utcnow())
    
    users_db[user_email] = profile_data
    
    return {"status": 200, "profile": profile_data}

@app.post("/api/v1/enrollments")
async def enroll_course(enrollment: EnrollmentRequest, request: Request):
    user_email = verify_token(request)
    if not user_email:
        return {"status": 401, "message": "Unauthorized"}
    
    enrollment_key = f"{user_email}_{enrollment.course_id}"
    
    if enrollment_key in enrollments_db:
        return {"status": 400, "message": "Already enrolled in this course"}
    
    enrollment_data = {
        "user_email": user_email,
        "course_id": enrollment.course_id,
        "enrolled_at": datetime.utcnow(),
        "status": "active"
    }
    
    enrollments_db[enrollment_key] = enrollment_data
    
    return {"status": 200, "enrollment": enrollment_data}

@app.get("/api/v1/enrollments")
async def get_enrollments(request: Request):
    user_email = verify_token(request)
    if not user_email:
        return {"status": 401, "message": "Unauthorized"}
    
    user_enrollments = [
        enrollment for enrollment in enrollments_db.values() 
        if enrollment["user_email"] == user_email
    ]
    
    return {"status": 200, "enrollments": user_enrollments}

@app.post("/api/v1/progress")
async def update_progress(progress: ProgressUpdate, request: Request):
    user_email = verify_token(request)
    if not user_email:
        return {"status": 401, "message": "Unauthorized"}
    
    progress_key = f"{user_email}_{progress.lesson_id}"
    
    progress_data = {
        "user_email": user_email,
        "lesson_id": progress.lesson_id,
        "progress": progress.progress,
        "completed": progress.completed,
        "updated_at": datetime.utcnow()
    }
    
    progress_db[progress_key] = progress_data
    
    return {"status": 200, "progress": progress_data}

@app.get("/api/v1/progress")
async def get_progress(request: Request):
    user_email = verify_token(request)
    if not user_email:
        return {"status": 401, "message": "Unauthorized"}
    
    user_progress = [
        progress for progress in progress_db.values() 
        if progress["user_email"] == user_email
    ]
    
    return {"status": 200, "progress": user_progress}

@app.get("/api/v1/progress/course/{course_id}")
async def get_course_progress(course_id: int, request: Request):
    user_email = verify_token(request)
    if not user_email:
        return {"status": 401, "message": "Unauthorized"}
    
    course_progress = []
    for progress in progress_db.values():
        if progress["user_email"] == user_email:
            course_progress.append(progress)
    
    return {"status": 200, "progress": course_progress}

@app.delete("/api/v1/enrollments/{course_id}")
async def unenroll_course(course_id: int, request: Request):
    user_email = verify_token(request)
    if not user_email:
        return {"status": 401, "message": "Unauthorized"}
    
    enrollment_key = f"{user_email}_{course_id}"
    
    if enrollment_key not in enrollments_db:
        return {"status": 404, "message": "Enrollment not found"}
    
    del enrollments_db[enrollment_key]
    
    return {"status": 200, "message": "Unenrolled successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
