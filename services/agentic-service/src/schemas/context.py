from pydantic import BaseModel, Field
from typing import List, Optional

class TestQA(BaseModel):
    question: str
    options: List[str]
    answer: int  # 1, 2, 3, or 4
    hint: str = ""
    explanation: str = ""
    difficulty: str = "medium"  # easy, medium, hard

class Lesson(BaseModel):
    lesson_id: str
    title: str
    overview: str
    content: str
    duration: int  # in minutes
    # Assessments for the lesson
    assessments: Optional[List[TestQA]] = None

class Roadmap(BaseModel):
    title: str
    description: str

class State(BaseModel):
    id: str
    difficulty: str
    duration: int
    title: Optional[str] = None
    description: Optional[str] = None
    roadmap: Optional[List[Roadmap]] = None
    lessons: Optional[List[Lesson]] = None
    user_id: Optional[str] = None
    s3_bucket: Optional[str] = None
    # Iterative lesson creation progress
    lessons_expected: Optional[int] = None
    next_lesson_index: Optional[int] = None


class StateResponse(BaseModel):
    id: str
    difficulty: str
    duration: int
    title: Optional[str] = None
    description: Optional[str] = None
    roadmap: Optional[List[Roadmap]] = None
    lessons: Optional[List[Lesson]] = None