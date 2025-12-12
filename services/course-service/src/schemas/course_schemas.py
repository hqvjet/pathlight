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
    course_id: Optional[str] = Field(default=None, description="Course ID to create; auto-generated if omitted")
    s3_key: Optional[List[str]] = Field(default=None, description="Array of S3 object keys to vectorize (optional)")
    user_position: Optional[str] = Field(default=None, description="User position / role")
    short_user_prompt: str = Field(..., description="Short prompt guiding course generation")
    course_duration: int = Field(..., description="Desired course duration in days")
    course_level: str = Field(..., description="overview | intermediate | advance")
    course_constraint: str = Field(..., description="professional | academic | friendly | humorous")
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
    answer: str
    explanation: str
    difficult_level_id: str | None = None


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


# ---- Lesson Test submission ----

class LessonTestSubmitAnswer(BaseModel):
    qa_id: str
    answer: str


class LessonTestSubmitRequest(BaseModel):
    answers: List[LessonTestSubmitAnswer]


class LessonTestSubmitResultItem(BaseModel):
    qa_id: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    difficulty: int | None = None
    gained_exp: int
    penalty_exp: int


class LessonTestSubmitResult(BaseModel):
    score: float
    correct_count: int
    total: int
    earned_exp: int
    penalty_exp: int
    applied_exp: int
    passed: bool
    pass_threshold: int
    level: int | None = None
    current_exp: int | None = None
    require_exp: int | None = None
    level_up: bool | None = None
    answers: List[LessonTestSubmitResultItem]


class LessonTestSubmitResponse(BaseModel):
    status: int
    result: LessonTestSubmitResult | None = None
    message: str | None = None


class FinalTestQA(BaseModel):
    final_qa_id: str
    question: str
    option1: str
    option2: str
    option3: str
    option4: str
    answer: str
    explanation: str


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


# ---- Upload presign schemas ----

class PresignUploadItem(BaseModel):
    filename: str
    content_type: str
    size: int


class PresignUploadRequest(BaseModel):
    items: List[PresignUploadItem]


class PresignUploadItemResponse(BaseModel):
    key: str
    upload_url: str
    headers: dict | None = None


class PresignUploadResponse(BaseModel):
    status: int
    items: List[PresignUploadItemResponse] | None = None
    message: str | None = None


# ---- Mutation request schemas ----

class FinishCourseRequest(BaseModel):
    course_id: str


class FinishLessonRequest(BaseModel):
    course_id: str
    lesson_id: str
