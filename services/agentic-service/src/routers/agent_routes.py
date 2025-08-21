"""
🛣️ File Routes - Reimagined

Clean, focused routes that showcase the new architecture.
Simple, elegant, and easy to understand.
"""

from fastapi import APIRouter
from controllers.file_controller import FileController
from schemas.vectorize_schemas import VectorizeRequest
from schemas.agent_schemas import AgentRequest, AgentResponse
from models.responses import VectorizationResponse
from controllers.agent_controller import AgentController


router = APIRouter(prefix="/agentic", tags=["files"])
file_controller = FileController()
agent_controller = AgentController()


@router.post("/vectorize", response_model=VectorizationResponse)
async def vectorize_files(request: VectorizeRequest) -> VectorizationResponse:
    """
    Process files from S3 and create embeddings for their content.
    
    This endpoint demonstrates the new clean architecture:
    - Controller orchestrates services
    - Services handle specific concerns
    - Clean error handling throughout
    
    Args:
        request: Vectorization request with file names and metadata
        
    Returns:
        VectorizationResponse with processing results and metrics
    """
    # Get files from S3
    s3_response = file_controller.get_files_by_names(request.uploaded_file)
    
    # Process files and create embeddings
    return await file_controller.vectorize_files(
        s3_response.file_streams, 
        request.id, 
        request.category
    )

@router.post("/course/generate", response_model=AgentResponse)
def generate_course(request: AgentRequest) -> AgentResponse:
    return agent_controller.generate_course(request)