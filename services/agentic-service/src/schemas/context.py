from pydantic import BaseModel, Field
from typing import List, Optional

class TestItem(BaseModel):
    test_id: str
    source_uri: str

class Lesson(BaseModel):
    lesson_id: str
    test: Optional[List[TestItem]]
    source_uri: str

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
    final_test: Optional[List[TestItem]] = None
    s3_bucket: Optional[str] = None