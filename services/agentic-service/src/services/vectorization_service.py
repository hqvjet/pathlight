"""
🔄 Vectorization Service

Orchestrates the complete file-to-vector pipeline.
The conductor that makes all the pieces work together beautifully.
"""

from datetime import datetime
from io import BytesIO
from typing import Dict, List

from core.logging import setup_logger, log_exception, log_structured
from core.exceptions import (
    ValidationError,
    ProcessingError,
    FileProcessingError,
    EmbeddingCreationError,
    PartialProcessingError,
)
from services.file_processor import FileProcessor
from services.embedding_service import EmbeddingService
from infrastructure.aws.opensearch_client import OpenSearchClient
from schemas.vectorize_schemas import MaterialData
from models.responses import VectorizationResponse, VectorizationWarning


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

    def vectorize_files(
        self,
        file_streams_dict: Dict[str, BytesIO],
        material_id: str,
        category: int,
        fail_on_any_error: bool = True,
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
        try:
            file_contents, processing_errors = self.file_processor.process_multiple_files(file_streams_dict)
        except FileProcessingError as e:
            # Re-raise as is – controller will map to HTTP 500
            log_exception(logger, "All files failed during processing", e)
            raise

        try:
            documents, embedding_errors = self.embedding_service.create_document_embeddings(file_contents)
        except EmbeddingCreationError as e:
            log_exception(logger, "Embedding creation failed for all documents", e)
            raise
        material_data = self.prepare_material_data(material_id, category, documents)

        # Index to OpenSearch if available
        if self.opensearch_client and self.opensearch_client.is_available():
            try:
                def index_single_chunk(doc, chunk):
                    payload = {
                        "id": str(material_data.id),
                        "category": int(material_data.category),
                        "documents": [
                            {
                                "document_id": int(doc.document_id),
                                "document_source": str(doc.document_source),
                                "chunks": [
                                    {
                                        "chunk_id": int(chunk.chunk_id),
                                        "chunk_text": str(chunk.chunk_text),
                                        "embedding": list(chunk.embedding),
                                    }
                                ],
                            }
                        ],
                    }
                    # Composite _id ensures uniqueness per chunk
                    composite_id = f"{material_id}:{int(doc.document_id)}:{int(chunk.chunk_id)}"
                    return self.opensearch_client.index_document(
                        self.opensearch_index_name,
                        payload,
                        composite_id,
                    )

                # Index chunks sequentially
                for doc in material_data.documents:
                    for chunk in doc.chunks:
                        try:
                            index_single_chunk(doc, chunk)
                        except Exception as e:
                            if not processing_errors:
                                processing_errors = []
                            processing_errors.append({
                                "opensearch": f"Indexing chunk failed: {str(e)}"
                            })
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
        else:
            logger.info("OpenSearch client not available - skipping indexing step")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()

        # Determine if we should convert warnings to an error response
        has_any_errors = bool(processing_errors or embedding_errors)
        if has_any_errors and (fail_on_any_error or len(documents) == 0):
            # Partial success (some documents) or total failure (should already have raised earlier)
            details = {
                "material_id": material_id,
                "category": category,
                "processing_errors": processing_errors,
                "embedding_errors": embedding_errors,
            }
            raise PartialProcessingError(
                message="Vectorization completed with errors",
                details=details,
            )

        # Prepare success (possibly with warnings) response
        response = VectorizationResponse(
            status=200,
            message="Vectorization completed successfully" if not has_any_errors else "Vectorization completed with warnings",
            material_id=material_id,
            category=category,
            total_documents=len(documents),
            total_chunks=sum(len(doc.chunks) for doc in documents),
            processed_files=len(file_contents),
            total_files=len(file_streams_dict),
            processing_time=processing_time,
        )

        if has_any_errors:
            response.warnings = VectorizationWarning(
                processing_errors=processing_errors or None,
                embedding_errors=embedding_errors or None,
            )

        log_structured(
            logger,
            'INFO',
            "Vectorization completed" if not has_any_errors else "Vectorization completed with warnings",
            material_id=material_id,
            total_documents=len(documents),
            total_chunks=sum(len(doc.chunks) for doc in documents),
            processing_time_seconds=f"{processing_time:.3f}",
            environment=self.opensearch_client.environment if self.opensearch_client else 'unknown',
            has_warnings=str(has_any_errors),
        )

        return response
