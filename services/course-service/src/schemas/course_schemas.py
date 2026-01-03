from pydantic import BaseModel, Field
from typing import Optional, List

class CreateCourseRequest(BaseModel):
    type: str = Field(
        default="GENERATE_COURSE_WITH_VECTORIZE",
        description="Job type required by SQS. Defaults to GENERATE_COURSE_WITH_VECTORIZE"
    )
    id: str = Field(default=None, description="Course ID to create; auto-generated if omitted")
    s3_keys: List[str] = Field(default=None, description="Array of S3 object keys (users/<user_id>/<file>)")
    user_id: str = Field(default=None, description="Owner user id; will be overridden by token if present")

    # Generation knobs (mapped to agentic-service payload)
    difficulty: str = Field(default="medium", description="easy | medium | hard")
    duration: int = Field(default=1200, description="Course duration (minutes)")

    class Config:
        populate_by_name = True


# ---- Course detail/list response schemas ----

class LessonInfo(BaseModel):
    lesson_id: str
    title: str
    finish: bool


class CourseFullInfo(BaseModel):
    title: str
    overview: str
    level: str
    duration: int
    publish: bool = False
    finish: bool = False
    user_id: str
    lesson: List[LessonInfo]
    progress_finished_lessons: int = 0
    progress_total_lessons: int = 0
    updated_at: str


class CourseFullInfoResponse(BaseModel):
    status: int
    info: CourseFullInfo


class CourseSummary(BaseModel):
    course_id: str
    title: str
    overview: str
    level: str
    duration: int
    finish: bool
    publish: bool = False
    user_id: str
    lesson_num: int
    finish_lesson_num: int
    updated_at: str


class CourseListResponse(BaseModel):
    status: int
    courses: List[CourseSummary]


class CourseVisibilityUpdate(BaseModel):
    course_id: str
    publish: bool = Field(..., alias="is_public")

    class Config:
        populate_by_name = True


# ---- Lesson detail ----

class LessonDetail(BaseModel):
    lesson_id: str
    course_id: str
    title: str
    overview: str
    content: str
    duration: int
    finish: bool
    locked: bool = False  # True if lesson is locked (previous lessons not completed)


class LessonListResponse(BaseModel):
    status: int
    lessons: List[LessonDetail]

# ---- Assessment (lesson-level questions) ----

class AssessmentItem(BaseModel):
    assessment_id: str
    lesson_id: str
    question: str
    hint: str | None = None
    has_hint: bool = False  # Flag to show hint button in UI
    explanation: str
    difficulty: str
    option1: str
    option2: str
    option3: str
    option4: str
    answer: int


class AssessmentListResponse(BaseModel):
    status: int
    assessments: List[AssessmentItem]


class AssessmentSubmitAnswer(BaseModel):
    assessment_id: str
    answer: int


class AssessmentSubmitRequest(BaseModel):
    answers: List[AssessmentSubmitAnswer]


class AssessmentSubmitResultItem(BaseModel):
    assessment_id: str
    selected_answer: int
    correct_answer: int
    is_correct: bool
    difficulty: str | None = None
    gained_exp: int
    penalty_exp: int


class AssessmentSubmitResult(BaseModel):
    score: float
    correct_count: int
    total: int
    earned_exp: int
    penalty_exp: int
    applied_exp: int
    passed: bool
    pass_threshold: int
    answers: List[AssessmentSubmitResultItem]


class ExperienceSnapshot(BaseModel):
    gained_exp: int
    new_level: int | None = None
    new_exp: int | None = None
    require_exp: int | None = None
    exp_needed_for_next: int | None = None
    rank: int | None = None


class AssessmentSubmitResponse(BaseModel):
    status: int
    result: AssessmentSubmitResult | None = None
    message: str | None = None
    experience: ExperienceSnapshot | None = None


# ---- Hint request schemas ----

class GetHintRequest(BaseModel):
    assessment_id: str


class GetHintResponse(BaseModel):
    status: int
    hint: str | None = None
    message: str | None = None
    exp_penalty: int = 0


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
