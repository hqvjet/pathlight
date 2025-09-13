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


# ---- Course detail/list response schemas ----

class LessonInfo(BaseModel):
    lesson_id: str
    title: str
    finish: bool


class CourseFullInfo(BaseModel):
    title: str
    description: str
    duration: int
    roadmap: Optional[str] = None
    lesson: List[LessonInfo]
    updated_at: str


class CourseFullInfoResponse(BaseModel):
    status: int
    info: CourseFullInfo


class CourseSummary(BaseModel):
    course_id: str
    title: str
    description: str
    duration: int
    lesson_num: int
    finish_lesson_num: int
    updated_at: str


class CourseListResponse(BaseModel):
    status: int
    courses: List[CourseSummary]
