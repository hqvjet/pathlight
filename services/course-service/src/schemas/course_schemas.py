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


# ---- Lesson / Test / Final Test detail schemas ----

class LessonDetail(BaseModel):
    lesson_id: str
    course_id: str
    title: str
    description: str
    content: str
    finish: bool


class LessonListResponse(BaseModel):
    status: int
    lessons: List[LessonDetail]


class LessonTestQA(BaseModel):
    qa_id: str
    question: str
    option1: str
    option2: str
    option3: str
    option4: str


class LessonTest(BaseModel):
    test_id: str
    title: str
    description: str
    duration: int
    exp: int
    finish: bool
    qas: List[LessonTestQA]


class LessonTestResponse(BaseModel):
    status: int
    test: LessonTest


class FinalTestQA(BaseModel):
    final_qa_id: str
    question: str
    option1: str
    option2: str
    option3: str
    option4: str


class FinalTestDetail(BaseModel):
    final_test_id: str
    title: str
    description: str
    duration: int
    exp: int
    qas: List[FinalTestQA]


class FinalTestResponse(BaseModel):
    status: int
    final_test: FinalTestDetail
