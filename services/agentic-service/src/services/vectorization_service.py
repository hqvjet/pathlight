"""
🔄 Vectorization Service

Orchestrates the complete file-to-vector pipeline.
The conductor that makes all the pieces work together beautifully.
"""

from datetime import datetime
from io import BytesIO
from typing import Dict, List
from fastapi import HTTPException

from core.logging import setup_logger, log_exception, log_structured
from core.exceptions import ValidationError, ProcessingError
from services.file_processor import FileProcessor
from services.embedding_service import EmbeddingService
from infrastructure.aws.opensearch_client import OpenSearchClient
from schemas.vectorize_schemas import MaterialData
from models.responses import VectorizationResponse


logger = setup_logger(__name__)


class VectorizationService:
    """Professional vectorization service orchestrating the complete pipeline."""
    
    def __init__(
        self, 
        file_processor: FileProcessor,
        embedding_service: EmbeddingService,
        opensearch_client: OpenSearchClient,
        opensearch_index_name: str
    ):
        """
        Initialize vectorization service.
        
        Args:
            file_processor: File processing service
            embedding_service: Embedding creation service
            opensearch_client: OpenSearch client
            opensearch_index_name: OpenSearch index name
        """
        self.file_processor = file_processor
        self.embedding_service = embedding_service
        self.opensearch_client = opensearch_client
        self.opensearch_index_name = opensearch_index_name

    def validate_inputs(self, file_streams_dict: Dict[str, BytesIO], material_id: str) -> None:
        """
        Validate vectorization inputs.
        
        Args:
            file_streams_dict: File streams to process
            material_id: Material identifier
            
        Raises:
            ValidationError: If inputs are invalid
        """
        if not file_streams_dict:
            raise ValidationError("No files provided for vectorization")
        
        if not material_id or not str(material_id).strip():
            raise ValidationError("Valid material ID is required")

    def prepare_material_data(self, material_id: str, category: int, documents: List) -> MaterialData:
        """
        Prepare material data for indexing.
        
        Args:
            material_id: Material identifier
            category: Material category
            documents: List of document data
            
        Returns:
            MaterialData instance
            
        Raises:
            ProcessingError: If data preparation fails
        """
        try:
            material_data = MaterialData(
                id=material_id,
                category=category,
                documents=documents
            )
            
            total_chunks = sum(len(doc.chunks) for doc in documents)
            logger.info(f"Created MaterialData with {len(documents)} documents and {total_chunks} chunks")
            
            return material_data
            
        except Exception as e:
            log_exception(logger, "Failed to create MaterialData object", e)
            raise ProcessingError(f"Failed to prepare data for indexing: {str(e)}")

    async def vectorize_files(
        self, 
        file_streams_dict: Dict[str, BytesIO], 
        material_id: str, 
        category: int
    ) -> VectorizationResponse:
        """
        Process file streams and create embeddings for text chunks.
        
        Args:
            file_streams_dict: Dictionary of filename -> file_stream
            material_id: Unique identifier for the material
            category: Category number for the material
            
        Returns:
            VectorizationResponse with processing results
            
        Raises:
            HTTPException: If critical errors occur during processing
        """
        start_time = datetime.now()
        logger.info(f"Starting vectorization process for {len(file_streams_dict)} files")
        logger.info(f"Material ID: {material_id}, Category: {category}")
        
        # Validate inputs
        self.validate_inputs(file_streams_dict, material_id)
        
        # Process files and create embeddings
        file_contents, processing_errors = await self.file_processor.process_multiple_files(file_streams_dict)
        documents, embedding_errors = await self.embedding_service.create_document_embeddings(file_contents)
        material_data = self.prepare_material_data(material_id, category, documents)
        
        # Index to OpenSearch if available
        try:
            await self.opensearch_client.index_material_data(
                self.opensearch_index_name, 
                material_data.model_dump(), 
                material_id
            )
        except Exception as e:
            log_exception(logger, "OpenSearch indexing failed", e)
            # Only add to warnings, don't fail the entire process unless in Lambda
            if self.opensearch_client.environment == 'lambda':
                # In Lambda/production, re-raise the exception
                raise
            else:
                # In local/dev, add to warnings and continue
                if not processing_errors:
                    processing_errors = []
                processing_errors.append({"opensearch": f"Indexing failed: {str(e)}"})
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare response
        response = VectorizationResponse(
            status=200,
            message="Vectorization completed successfully",
            material_id=material_id,
            category=category,
            total_documents=len(documents),
            total_chunks=sum(len(doc.chunks) for doc in documents),
            processed_files=len(file_contents),
            total_files=len(file_streams_dict),
            processing_time=processing_time
        )
        
        # Include warnings if any errors occurred
        if processing_errors or embedding_errors:
            response.warnings = {
                "processing_errors": processing_errors if processing_errors else None,
                "embedding_errors": embedding_errors if embedding_errors else None
            }
        
        # Log completion with structured format
        log_structured(
            logger, 'INFO', "Vectorization completed", 
            material_id=material_id, 
            total_documents=len(documents),
            total_chunks=sum(len(doc.chunks) for doc in documents),
            processing_time_seconds=f"{processing_time:.3f}",
            environment=self.opensearch_client.environment
        )
        
        return response
