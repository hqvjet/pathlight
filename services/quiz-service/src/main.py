from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import jwt
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quiz Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
JWT_ALGORITHM = "HS256"

class Quiz(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    questions: List[Dict[str, Any]]
    time_limit: int
    difficulty: str
    category: str
    created_at: Optional[datetime] = None

class QuizAttempt(BaseModel):
    id: Optional[int] = None
    quiz_id: int
    user_email: str
    answers: List[Dict[str, Any]]
    score: int
    completed_at: Optional[datetime] = None

quizzes_db = {}
attempts_db = {}
quiz_counter = 1
attempt_counter = 1

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
    return {"message": "Quiz Service đang chạy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "quiz-service"}

@app.get("/api/v1/quizzes")
async def get_quizzes(category: Optional[str] = None, difficulty: Optional[str] = None):
    quizzes = list(quizzes_db.values())
    
    if category:
        quizzes = [q for q in quizzes if q["category"] == category]
    if difficulty:
        quizzes = [q for q in quizzes if q["difficulty"] == difficulty]
    
    return {"status": 200, "quizzes": quizzes}

@app.post("/api/v1/quizzes")
async def create_quiz(quiz: Quiz, request: Request):
    global quiz_counter
    user = verify_token(request)
    if not user:
        return {"status": 401, "message": "Unauthorized"}
    
    quiz_data = quiz.dict()
    quiz_data["id"] = quiz_counter
    quiz_data["created_at"] = datetime.utcnow()
    quizzes_db[quiz_counter] = quiz_data
    quiz_counter += 1
    
    return {"status": 200, "quiz": quiz_data}

@app.get("/api/v1/quizzes/{quiz_id}")
async def get_quiz(quiz_id: int):
    if quiz_id not in quizzes_db:
        return {"status": 404, "message": "Quiz not found"}
    
    return {"status": 200, "quiz": quizzes_db[quiz_id]}

@app.post("/api/v1/quizzes/{quiz_id}/attempt")
async def attempt_quiz(quiz_id: int, attempt: QuizAttempt, request: Request):
    global attempt_counter
    user = verify_token(request)
    if not user:
        return {"status": 401, "message": "Unauthorized"}
    
    if quiz_id not in quizzes_db:
        return {"status": 404, "message": "Quiz not found"}
    
    attempt_data = attempt.dict()
    attempt_data["id"] = attempt_counter
    attempt_data["quiz_id"] = quiz_id
    attempt_data["user_email"] = user
    attempt_data["completed_at"] = datetime.utcnow()
    attempts_db[attempt_counter] = attempt_data
    attempt_counter += 1
    
    return {"status": 200, "attempt": attempt_data}

@app.get("/api/v1/user/quiz-attempts")
async def get_user_attempts(request: Request):
    user = verify_token(request)
    if not user:
        return {"status": 401, "message": "Unauthorized"}
    
    user_attempts = [attempt for attempt in attempts_db.values() if attempt["user_email"] == user]
    return {"status": 200, "attempts": user_attempts}

@app.get("/api/v1/quizzes/{quiz_id}/leaderboard")
async def get_leaderboard(quiz_id: int):
    if quiz_id not in quizzes_db:
        return {"status": 404, "message": "Quiz not found"}
    
    quiz_attempts = [attempt for attempt in attempts_db.values() if attempt["quiz_id"] == quiz_id]
    leaderboard = sorted(quiz_attempts, key=lambda x: x["score"], reverse=True)[:10]
    
    return {"status": 200, "leaderboard": leaderboard}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
