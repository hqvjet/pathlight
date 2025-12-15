from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class CreateQuizRequest(BaseModel):
    type: str = Field(default="generate_quiz", description="Job type required by SQS")
    short_prompt: str = Field(..., alias="short_prompt", description="Short prompt guiding quiz generation")
    user_role: Optional[str] = Field(default=None, alias="user_role", description="User role/position")
    course_duration: int = Field(..., description="Desired quiz duration in days")
    course_level: str = Field(..., description="overview | intermediate | advance")
    course_constraint: str = Field(..., description="professional | academic | friendly | humorous")
    quiz_id: Optional[str] = Field(default=None, description="Quiz ID to create; auto-generated if omitted")
    documents: Optional[List[str]] = Field(default=None, alias="documents", description="Array of S3 object keys (users/<user_id>/<file>)")
    user_id: Optional[str] = Field(default=None, description="Owner user id; will be overridden by token if present")
    # legacy/compat fields (still honored)
    s3_key: Optional[List[str]] = Field(default=None, description="Array of S3 object keys to vectorize (optional)")
    user_position: Optional[str] = Field(default=None, description="Legacy: user position / role")
    short_user_prompt: Optional[str] = Field(default=None, description="Legacy short prompt")
    difficulty: str = Field(default="medium")
    duration: int = Field(default=1200)

    model_config = ConfigDict(populate_by_name=True)


class QuizCardItem(BaseModel):
    card_id: str
    quiz_id: str
    question: str
    hint: Optional[str] = None
    explanation: str
    difficulty: str
    option1: str
    option2: str
    option3: str
    option4: str


class QuizDetail(BaseModel):
    quiz_id: str
    title: str
    overview: str
    level: str
    duration: int
    publish: bool
    finish: bool
    num_questions: int
    previous_score: Optional[int] = None
    owner_id: str
    created_at: str
    cards: List[QuizCardItem]


class QuizDetailResponse(BaseModel):
    status: int
    quiz: QuizDetail


class QuizSummary(BaseModel):
    quiz_id: str
    title: str
    overview: str
    level: str
    duration: int
    publish: bool
    finish: bool
    num_questions: int
    previous_score: Optional[int] = None
    owner_id: str
    created_at: str


class QuizListResponse(BaseModel):
    status: int
    quizzes: List[QuizSummary]


class QuizSubmitAnswer(BaseModel):
    card_id: str
    answer: int = Field(..., ge=1, le=4)


class QuizSubmitRequest(BaseModel):
    answers: List[QuizSubmitAnswer]


class QuizSubmitResultItem(BaseModel):
    card_id: str
    selected_answer: int
    correct_answer: int
    is_correct: bool
    difficulty: Optional[str] = None
    explanation: Optional[str] = None


class QuizSubmitResult(BaseModel):
    score: float
    correct_count: int
    total: int
    answers: List[QuizSubmitResultItem]


class QuizSubmitResponse(BaseModel):
    status: int
    result: Optional[QuizSubmitResult] = None
    message: Optional[str] = None


class QuizVisibilityUpdate(BaseModel):
    quiz_id: str
    publish: bool = Field(..., alias="is_public")
    model_config = ConfigDict(populate_by_name=True)


class FinishQuizRequest(BaseModel):
    quiz_id: str
