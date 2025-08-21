"""
🎮 File Controller - Reimagined

A clean, focused controller that orchestrates file operations beautifully.
No more 900+ line monsters - just elegant coordination.
"""

from io import BytesIO
from typing import List, Dict, Any
from fastapi import HTTPException

from core.logging import setup_logger, log_exception, log_structured
from core.environment import get_environment_type
from infrastructure.aws.s3_client import S3Client
from infrastructure.aws.opensearch_client import OpenSearchClient
from infrastructure.openai.client import OpenAIClient
from infrastructure.clients import clients as shared_clients
from services.file_processor import FileProcessor
from services.embedding_service import EmbeddingService
from services.vectorization_service import VectorizationService
from config.file_config import FileProcessingConfig
from models.responses import VectorizationResponse, S3FileResponse
from config import config


logger = setup_logger(__name__)


class FileController:
    """
    Professional file controller with clean service orchestration.
    
    This controller focuses on coordination rather than implementation.
    All the heavy lifting is done by dedicated services.
    """
    
    def __init__(self, s3_client: S3Client | None = None, opensearch_client: OpenSearchClient | None = None, openai_client: OpenAIClient | None = None):
        """Initialize FileController with injected service dependencies."""
        logger.info("Initializing FileController...")

        self.environment = get_environment_type()
        logger.info(f"Detected environment: {self.environment}")

        # Load configuration
        self.config = FileProcessingConfig.from_app_config(config)

        # Use shared clients by default, allow overrides via DI
        self.s3_client = s3_client or shared_clients.s3
        self.opensearch_client = opensearch_client or shared_clients.opensearch
        self.openai_client = openai_client or shared_clients.openai
        
        # Initialize services
        self.file_processor = FileProcessor(self.config.allowed_extensions)
        self.embedding_service = EmbeddingService(self.openai_client, self.config.max_tokens_per_chunk)
        self.vectorization_service = VectorizationService(
            self.file_processor,
            self.embedding_service,
            self.opensearch_client,
            self.config.opensearch_index_name
        )
        
        logger.info("FileController initialization completed successfully")

    # Note: S3 client is now provided via DI/shared clients

    # Note: OpenSearch client is now provided via DI/shared clients

    # Note: OpenAI client is now provided via DI/shared clients

    def get_files_by_names(self, file_names: List[str]) -> S3FileResponse:
        """
        Retrieve multiple files from S3 by their names.
        
        Args:
            file_names: List of file names to retrieve from S3
            
        Returns:
            S3FileResponse with file streams and metadata
            
        Raises:
            HTTPException: If S3 operations fail
        """
        logger.info(f"Starting file retrieval for {len(file_names)} files: {file_names}")
        
        # Validation
        if not config.S3_BUCKET_NAME:
            raise HTTPException(
                status_code=500, 
                detail="S3 bucket name not configured. Please set AWS_S3_BUCKET_NAME environment variable."
            )

        if not file_names:
            raise HTTPException(
                status_code=400,
                detail="No file names provided"
            )

        # Use S3 client to retrieve files
        result = self.s3_client.get_multiple_files(
            bucket_name=config.S3_BUCKET_NAME,
            filenames=file_names,
            max_size_bytes=self.config.max_file_size_bytes
        )
        
        # Handle the case where all files failed
        if result["failed_files"] and not result["file_streams"]:
            error_code = 404 if any("not found" in f["error"] for f in result["failed_files"]) else 500
            raise HTTPException(
                status_code=error_code,
                detail={
                    "message": "All files failed to retrieve",
                    "failed_files": result["failed_files"],
                    "total_failed": result["total_failed"]
                }
            )

        return S3FileResponse(
            file_streams=result["file_streams"],
            file_metadata=result["file_metadata"],
            failed_files=result["failed_files"],
            total_successful=result["total_successful"],
            total_failed=result["total_failed"]
        )

    async def vectorize_files(
        self, 
        file_streams_dict: Dict[str, BytesIO], 
        material_id: str, 
        category: int
    ) -> VectorizationResponse:
        """
        Process file streams and create embeddings for text chunks.
        
        Args:
            file_streams_dict: Dictionary of filename -> file_stream from S3
            material_id: Unique identifier for the material
            category: Category number for the material
            
        Returns:
            VectorizationResponse with processing results
            
        Raises:
            HTTPException: If critical errors occur during processing
        """
        try:
            return await self.vectorization_service.vectorize_files(
                file_streams_dict, material_id, category
            )
        except Exception as e:
            log_exception(logger, "Vectorization process failed", e)
            raise HTTPException(
                status_code=500,
                detail=f"Vectorization failed: {str(e)}"
            )
