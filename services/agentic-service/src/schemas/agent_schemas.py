from pydantic import BaseModel, Field
from typing import List

class AgentRequest(BaseModel):
    id: str = Field(..., description="ID of the Course/Quiz for retrieval and saving")
    difficulty: str = Field(..., description="Difficulty level for course planning (e.g., easy, medium, hard)")
    duration: int = Field(..., description="Target duration in seconds (e.g., 1200 for 20 minutes)")
    user_id: str | None = Field(None, description="Owner user id for persistence and authorization")

class TestResponse(BaseModel):
    source_uri: str = Field(..., description="ID of the generated test")

class LessonResponse(BaseModel):
    source_uri: str = Field(..., description="ID of the generated lesson")
    test_source_uri: List[TestResponse] = Field(..., description="List of tests associated with the lesson")

class AgentResponse(BaseModel):
    title: str = Field(..., description="Title of the Course/Quiz")
    description: str = Field(..., description="Description of the Course/Quiz")
    roadmap: List[str] = Field(..., description="Roadmap of the Course/Quiz")
    lessons: List[LessonResponse] = Field(..., description="Lessons included in the Course/Quiz")
    final_test: List[TestResponse] = Field(..., description="Final test for the Course/Quiz")
    s3_bucket: str = Field(..., description="S3 bucket where the Course/Quiz is stored")

# Tool schemas
class RetrievalArgs(BaseModel):
    """Arguments for retrieval tool with strict schema for OpenAI."""
    model_config = {"extra": "forbid"}  # Strict mode: no additional properties
    
    id: str = Field(..., description="ID of the Course/Quiz for retrieval")
    query: str = Field(..., description="Query string for the retrieval")
    k: int = Field(..., description="Number of results to return")