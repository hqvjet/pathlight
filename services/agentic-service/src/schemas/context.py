from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class TestQA(BaseModel):
    question: str
    options: List[str]
    answer: int  # 1, 2, 3, or 4
    hint: str = ""
    explanation: str = ""
    difficulty: str = "medium"  # easy, medium, hard
    
    @field_validator('answer')
    @classmethod
    def validate_answer(cls, v):
        if not isinstance(v, int) or not (1 <= v <= 4):
            raise ValueError(f'answer must be int between 1-4, got {v}')
        return v
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        if not isinstance(v, list) or len(v) != 4:
            raise ValueError(f'options must be list of 4 items, got {len(v) if isinstance(v, list) else "not list"}')
        return v

class Lesson(BaseModel):
    lesson_id: str
    title: str
    overview: str
    content: str
    duration: int  # in minutes
    # Assessments for the lesson
    assessments: Optional[List[TestQA]] = None
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or len(v.strip()) < 100:
            raise ValueError(f'content must be at least 100 chars, got {len(v) if v else 0}')
        # Cap at 600 to prevent token bloat
        if len(v) > 600:
            return v[:600] + "\n(truncated)"
        return v

class Roadmap(BaseModel):
    """Roadmap item - mỗi item là 1 cột mốc/module/lesson plan"""
    title: str = Field(..., description="Tên cột mốc/module")
    description: str = Field(..., description="Mô tả ngắn gọn nội dung")

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