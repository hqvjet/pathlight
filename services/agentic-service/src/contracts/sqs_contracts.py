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


class BaseMessage(BaseModel):
  type: MessageType
  correlation_id: str = Field(..., description="Correlation id for tracing")
  timestamp: str


class GenerateCourseWithVectorizePayload(BaseModel):
  id: str
  difficulty: str
  duration: int
  s3_keys: List[str]


class GenerateCourseWithVectorizeMessage(BaseMessage):
  payload: GenerateCourseWithVectorizePayload


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
