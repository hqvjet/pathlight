from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class CreateQuizRequest(BaseModel):
    type: str = Field(default="generate_quiz", description="Job type required by SQS")
    duration: int = Field(..., description="Desired quiz duration in minutes")
    level: str = Field(..., description="easy | medium | hard")
    quiz_id: Optional[str] = Field(default=None, description="Quiz ID to create; auto-generated if omitted")
    documents: Optional[List[str]] = Field(default=None, alias="documents", description="Array of S3 object keys (users/<user_id>/<file>)")
    user_id: Optional[str] = Field(default=None, description="Owner user id; will be overridden by token if present")
    num_questions: Optional[int] = Field(default=10, description="Number of quiz questions to generate")
    s3_key: Optional[List[str]] = Field(default=None, description="Array of S3 object keys to vectorize (optional)")

    model_config = ConfigDict(populate_by_name=True)


class ManualQuizCard(BaseModel):
    question: str
    hint: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: str = Field(default="easy", description="easy | medium | hard")
    option1: str
    option2: str
    option3: str
    option4: str
    answer: int = Field(..., ge=1, le=4, description="Correct answer number (1-4)")


class CreateManualQuizRequest(BaseModel):
    title: str
    overview: str
    level: str = Field(default="easy", description="easy | medium | hard")
    duration: int = Field(default=15, description="Duration in minutes")
    cards: List[ManualQuizCard]

    model_config = ConfigDict(populate_by_name=True)


class QuizCardItem(BaseModel):
    card_id: str
    quiz_id: str
    question: str
    hint: Optional[str] = Field(default=None)
    explanation: Optional[str] = Field(default=None)
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
    experience: Optional[dict] = None


class QuizVisibilityUpdate(BaseModel):
    quiz_id: str
    publish: bool = Field(..., alias="is_public")
    model_config = ConfigDict(populate_by_name=True)


class FinishQuizRequest(BaseModel):
    quiz_id: str


class FinishQuizResponse(BaseModel):
    status: int
    message: str
    experience: dict


class StartQuizRequest(BaseModel):
    quiz_id: str


class StartQuizResponse(BaseModel):
    status: int
    message: str
    quiz_id: str
    started_at: str
