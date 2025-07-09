from pydantic import BaseModel, Field
from typing import List

class VectorizeRequest(BaseModel):
    id: str = Field(..., description="ID of course/quiz depend on the category")
    category: int = Field(..., description="Category to identify course(0) or quiz(1)")
    uploaded_file: List[str]

class ChunkData(BaseModel):
    """Schema for individual chunk data in OpenSearch requests"""
    chunk_id: int = Field(..., description="Unique identifier for the chunk")
    embedding: List[float] = Field(..., description="Vector embedding of the chunk")
    chunk_text: str = Field(..., description="Text content of the chunk")

class DocumentData(BaseModel):
    """Schema for document data in OpenSearch requests"""
    document_id: int = Field(..., description="Unique identifier for the document")
    document_source: str = Field(..., description="Source of the document")
    chunks: List[ChunkData] = Field(..., description="List of text chunks with embeddings")

class MaterialData(BaseModel):
    """Schema for individual chunk data in OpenSearch requests"""
    id: str = Field(..., description="ID of course/quiz depend on the category")
    category: int = Field(..., description="Category of the Material, maybe course(0) or quiz(1)")
    documents: List[DocumentData] = Field(..., description="List of documents of the material")