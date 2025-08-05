from pydantic import BaseModel
from typing import Optional

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None
    total_questions: Optional[int] = None

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    total_questions: Optional[int] = None
