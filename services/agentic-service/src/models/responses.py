"""
📊 Response Models

Clean, well-defined response models for API endpoints.
Clear data structures that speak for themselves.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, validator


class FileProcessingResult(BaseModel):
    """Result of a file processing operation."""
    filename: str
    success: bool
    error: Optional[str] = None
    content_length: Optional[int] = None
    chunks_count: Optional[int] = None

    @validator('filename')
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        return v.strip()


class VectorizationResponse(BaseModel):
    """Response for vectorization operations."""
    status: int
    message: str
    material_id: str
    category: int
    total_documents: int
    total_chunks: int
    processed_files: int
    total_files: int
    processing_time: float
    warnings: Optional[Dict[str, Any]] = None


class S3FileResponse(BaseModel):
    """Response for S3 file operations."""
    file_streams: Dict[str, Any]
    file_metadata: Dict[str, Dict[str, Any]]
    failed_files: Optional[list] = None
    total_successful: int
    total_failed: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
    timestamp: str
    environment: str
    services: Dict[str, str]
