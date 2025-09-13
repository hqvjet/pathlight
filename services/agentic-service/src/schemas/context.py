from pydantic import BaseModel, Field
from typing import List, Optional

class TestQA(BaseModel):
    question: str
    options: List[str]
    answer: str
    explaination: str

class Lesson(BaseModel):
    lesson_id: str
    lesson_name: Optional[str] = None
    lesson_description: Optional[str] = None
    lesson_content: Optional[str] = None
    # Full in-memory tests for the lesson
    tests: Optional[List[TestQA]] = None

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
    # Final test content for the whole course
    final_test: Optional[List[TestQA]] = None
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
    final_test: Optional[List[TestQA]] = None