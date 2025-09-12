from pydantic import BaseModel, Field
from typing import Optional, List

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


class CreateCourseRequest(BaseModel):
    course_id: str = Field(..., description="Course ID to create")
    s3_key: List[str] = Field(..., description="Array of S3 object keys to vectorize")
    difficulty: str = Field(default="medium")
    duration: int = Field(default=1200)
