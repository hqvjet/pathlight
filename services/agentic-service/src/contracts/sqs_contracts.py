"""
SQS message contracts for agentic-service.

Messages are JSON objects sent to an SQS queue triggering the Lambda.

Required fields (common):
- type: str  -> one of ["GENERATE_COURSE_WITH_VECTORIZE"]
- correlation_id: str -> id for tracing/log correlation (e.g., request id)
- timestamp: str -> ISO8601 creation time

Type-specific payloads:

1) GENERATE_COURSE_WITH_VECTORIZE
{
  "type": "GENERATE_COURSE_WITH_VECTORIZE",
  "correlation_id": "...",
  "timestamp": "...",
  "payload": {
    "id": "course-id",
    "difficulty": "easy|medium|hard",
    "duration": 1200,
    "s3_keys": ["path/to/file1.pdf", "path/to/file2.docx"]
  }
}
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MessageType(str, Enum):
  GENERATE_COURSE_WITH_VECTORIZE = "GENERATE_COURSE_WITH_VECTORIZE"
  CHATBOT_QUESTION = "CHATBOT_QUESTION"
  GENERATE_QUIZ_WITH_VECTORIZE = "GENERATE_QUIZ_WITH_VECTORIZE"
  RECOMMEND_COURSES = "RECOMMEND_COURSES"
  RECOMMEND_QUIZZES = "RECOMMEND_QUIZZES"


class BaseMessage(BaseModel):
  type: MessageType
  correlation_id: str = Field(..., description="Correlation id for tracing")
  timestamp: str


class GenerateCourseWithVectorizePayload(BaseModel):
  id: str
  difficulty: str
  duration: int
  s3_keys: List[str]
  user_id: str


class GenerateCourseWithVectorizeMessage(BaseMessage):
  payload: GenerateCourseWithVectorizePayload


class ChatbotQuestionPayload(BaseModel):
  chat_id: str
  message: str
  lesson_id: str
  course_id: str
  user_id: str


class ChatbotQuestionMessage(BaseMessage):
  payload: ChatbotQuestionPayload


class GenerateQuizWithVectorizePayload(BaseModel):
  id: str  # quiz_id
  difficulty: str
  duration: int
  num_questions: int
  s3_keys: List[str]
  user_id: str


class GenerateQuizWithVectorizeMessage(BaseMessage):
  payload: GenerateQuizWithVectorizePayload


class RecommendCoursesPayload(BaseModel):
  sim_id: str  # Unique search ID from course service
  user_id: str  # User to get recommendations for
  topk: int  # Number of recommendations to return
  course_ids: List[str]  # List of course IDs to search within (public courses)


class RecommendCoursesMessage(BaseMessage):
  payload: RecommendCoursesPayload


class RecommendQuizzesPayload(BaseModel):
  sim_id: str  # Unique search ID from quiz service
  user_id: str  # User to get recommendations for
  topk: int  # Number of recommendations to return
  quiz_ids: List[str]  # List of quiz IDs to search within (public quizzes)


class RecommendQuizzesMessage(BaseMessage):
  payload: RecommendQuizzesPayload


class SQSBatchResponse(BaseModel):
  batchItemFailures: List[dict] = Field(default_factory=list)


# --- AWS SQS Event (minimal schema we actually use) ---

class SQSRecord(BaseModel):
  messageId: str
  body: str
  receiptHandle: Optional[str] = None
  attributes: Optional[Dict[str, Any]] = None
  messageAttributes: Optional[Dict[str, Any]] = None
  md5OfBody: Optional[str] = None
  eventSource: Optional[str] = None
  eventSourceARN: Optional[str] = None
  awsRegion: Optional[str] = None


class SQSEvent(BaseModel):
  Records: List[SQSRecord]
