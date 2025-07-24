from pydantic import BaseModel
from typing import Optional

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    instructor: Optional[str] = None
    duration: Optional[int] = None
    level: Optional[str] = None
    price: Optional[float] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    duration: Optional[int] = None
    level: Optional[str] = None
    price: Optional[float] = None
