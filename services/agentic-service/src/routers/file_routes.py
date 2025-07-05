from fastapi import APIRouter, Query
from typing import List

from controllers import FileController


router = APIRouter(prefix="/agentic", tags=["files"])
file_controller = FileController()


@router.post("/vectorize")
async def vectorize_files(file_names: List[str]):
    """
    Process files from S3 and create embeddings for their content.
    
    Accepts: List of file names (PDF, DOCX, PPTX files) existing in S3
    Returns: Embeddings for text chunks extracted from files
    """
    file_stream = file_controller.get_files_by_names(file_names)['file_stream']
    return await file_controller.vectorize_files(file_stream)