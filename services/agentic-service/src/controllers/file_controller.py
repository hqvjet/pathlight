import logging
import traceback
import asyncio
import functools
import os
from datetime import datetime
from fastapi import HTTPException
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass
import openai
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from io import BytesIO
from opensearchpy import OpenSearch, OpenSearchException
from requests.exceptions import Timeout, ConnectionError
from pydantic import BaseModel, validator

from services.file_service import extract_content_with_tags
from services.text_service import split_into_chunks
from schemas.vectorize_schemas import ChunkData, DocumentData, MaterialData
from config import config


# Configure logger with structured formatting for Lambda
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Ensure we have a proper formatter that handles multi-line logs
def setup_logger():
    """Setup logger with proper formatting for different environments."""
    if not logger.handlers:
        # Check if we're in Lambda environment
        is_lambda = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
        
        handler = logging.StreamHandler()
        
        if is_lambda:
            # Lambda-friendly format (single line with escaped newlines)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            # Local development format (multi-line friendly)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False


# Setup logger on import
setup_logger()


def log_exception(logger_instance: logging.Logger, message: str, exception: Exception) -> None:
    """Simple single-line exception logging for all environments."""
    # Always use single line format to avoid Lambda log splitting
    logger_instance.error(f"{message}: {type(exception).__name__}: {str(exception)}")


def log_structured(logger_instance: logging.Logger, level: str, message: str, **kwargs) -> None:
    """Simple structured logging for all environments."""
    # Simple single-line structured log
    log_parts = [message]
    for key, value in kwargs.items():
        log_parts.append(f"{key}={value}")
    
    log_line = " | ".join(log_parts)
    getattr(logger_instance, level.lower())(log_line)


# Custom Exceptions
class FileControllerError(Exception):
    """Base exception for FileController errors."""
    pass


class S3ConfigurationError(FileControllerError):
    """Raised when S3 configuration is invalid."""
    pass


class OpenSearchConfigurationError(FileControllerError):
    """Raised when OpenSearch configuration is invalid."""
    pass


class FileProcessingError(FileControllerError):
    """Raised when file processing fails."""
    pass


class EmbeddingCreationError(FileControllerError):
    """Raised when embedding creation fails."""
    pass


class ValidationError(FileControllerError):
    """Raised when input validation fails."""
    pass


# Configuration and Response Models
@dataclass
class FileControllerConfig:
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = None
    max_tokens_per_chunk: int = 512
    opensearch_index_name: str = None
    max_retries: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0

    def __post_init__(self):
        self.allowed_extensions = getattr(config, 'ALLOWED_FILE_EXTENSIONS', [])
        self.max_tokens_per_chunk = getattr(config, 'MAX_TOKENS_PER_CHUNK', 512)
        self.opensearch_index_name = getattr(config, 'OPENSEARCH_INDEX_NAME', None)
        self._validate_config()

    def _validate_config(self):
        if not self.allowed_extensions:
            raise ValueError("ALLOWED_FILE_EXTENSIONS must be configured")


class FileProcessingResult(BaseModel):
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


# Retry Decorator
def async_retry(
    max_retries: int = 3,
    exceptions: Tuple[type, ...] = (Exception,),
    backoff_factor: float = 2.0,
    base_delay: float = 1.0
):
    """Retry decorator for async functions with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
            return None
        return wrapper
    return decorator


class FileController:
    """
    Professional file controller for handling S3 operations, content extraction, 
    and vectorization with comprehensive error handling and logging.
    """
    
    def __init__(self):
        """Initialize FileController with proper error handling and logging."""
        logger.info("Initializing FileController...")
        
        # Detect environment
        self.environment = get_environment_type()
        logger.info(f"Detected environment: {self.environment}")
        
        self.config = FileControllerConfig()
        self.openai_client = self._initialize_openai_client()
        self.s3_client = self._initialize_s3_client()
        
        # Initialize OpenSearch only in appropriate environments
        self.opensearch_client = self._initialize_opensearch_client_conditional()
        
        logger.info("FileController initialization completed successfully")

    def _initialize_openai_client(self) -> openai.OpenAI:
        """Initialize OpenAI client with validation."""
        try:
            if not config.OPENAI_API_KEY:
                raise ValidationError("OPENAI_API_KEY is not configured")
            
            client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            logger.info("OpenAI client configured successfully")
            return client
            
        except Exception as e:
            log_exception(logger, "Failed to configure OpenAI client", e)
            raise HTTPException(
                status_code=500,
                detail="OpenAI configuration error. Please check API key configuration."
            )
        
    def _initialize_s3_client(self) -> boto3.client:
        """Initialize S3 client with proper error handling."""
        try:
            logger.info("Initializing S3 client...")
            
            if not config.REGION:
                raise S3ConfigurationError("AWS region is not configured")
            
            if config.ACCESS_KEY_ID and config.SECRET_ACCESS_KEY:
                logger.info("Using provided AWS credentials")
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=config.ACCESS_KEY_ID,
                    aws_secret_access_key=config.SECRET_ACCESS_KEY,
                    region_name=config.REGION
                )
            else:
                logger.info("Using default AWS credentials (IAM role, etc.)")
                s3_client = boto3.client('s3', region_name=config.REGION)
            
            self._test_s3_connection(s3_client)
            logger.info("S3 client initialized successfully")
            return s3_client
                
        except S3ConfigurationError:
            raise
        except Exception as e:
            log_exception(logger, "Unexpected error initializing S3 client", e)
            raise S3ConfigurationError(f"Failed to initialize S3 client: {str(e)}")

    def _test_s3_connection(self, s3_client: boto3.client) -> None:
        """Test S3 connection."""
        try:
            s3_client.list_buckets()
        except ClientError as e:
            error_code = e.response['Error']['Code']
            log_exception(logger, f"S3 connection test failed with error code {error_code}", e)
            if error_code in ['InvalidAccessKeyId', 'SignatureDoesNotMatch']:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid AWS credentials. Please check ACCESS_KEY_ID and SECRET_ACCESS_KEY."
                )
            raise
        except BotoCoreError as e:
            log_exception(logger, "S3 connection test failed with BotoCore error", e)
            raise HTTPException(
                status_code=500,
                detail="AWS service configuration error. Please check your AWS settings."
            )

    def _initialize_opensearch_client_conditional(self) -> Optional[OpenSearch]:
        """Initialize OpenSearch client based on environment conditions."""
        try:
            # Skip OpenSearch initialization in local environment if configured
            if self.environment == 'local' and not getattr(config, 'FORCE_OPENSEARCH_LOCAL', False):
                logger.info("Running in local environment - skipping OpenSearch initialization")
                logger.info("Set FORCE_OPENSEARCH_LOCAL=true to enable OpenSearch in local development")
                return None
            
            # Check if OpenSearch is explicitly disabled
            if not getattr(config, 'OPENSEARCH_ENABLED', True):
                logger.info("OpenSearch is disabled via configuration")
                return None
            
            # Check if running in test environment
            if os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('TESTING'):
                logger.info("Running in test environment - skipping OpenSearch initialization")
                return None
            
            return self._initialize_opensearch_client()
            
        except Exception as e:
            logger.warning(f"OpenSearch initialization failed, continuing without it: {e}")
            return None

    def _initialize_opensearch_client(self) -> Optional[OpenSearch]:
        """Initialize Opensearch client with proper error handling."""
        try:
            logger.info(f"Initializing Opensearch client with host: {getattr(config, 'OPENSEARCH_HOST', 'Not configured')}")
            
            # Validate required configuration
            required_configs = [
                (getattr(config, 'OPENSEARCH_HOST', None), "OPENSEARCH_HOST"),
                (getattr(config, 'OPENSEARCH_PORT', None), "OPENSEARCH_PORT"),
                (getattr(config, 'OPENSEARCH_USER', None), "OPENSEARCH_USER"),
                (getattr(config, 'OPENSEARCH_PASSWORD', None), "OPENSEARCH_PASSWORD")
            ]
            
            missing_configs = [name for value, name in required_configs if not value]
            if missing_configs:
                raise OpenSearchConfigurationError(f"Missing OpenSearch configuration: {', '.join(missing_configs)}")
            
            opensearch_client = OpenSearch(
                hosts=[{
                    'host': config.OPENSEARCH_HOST,
                    'port': config.OPENSEARCH_PORT
                }],
                http_auth=(config.OPENSEARCH_USER, config.OPENSEARCH_PASSWORD),
                use_ssl=getattr(config, 'OPENSEARCH_USE_SSL', True),
                verify_certs=getattr(config, 'OPENSEARCH_VERIFY_CERTS', True),
                connection_class=None,
                timeout=getattr(config, 'OPENSEARCH_TIMEOUT', 60),
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test the connection with timeout for local environments
            connection_timeout = 5 if self.environment == 'local' else 30
            return self._test_opensearch_connection(opensearch_client, connection_timeout)
                
        except OpenSearchConfigurationError as e:
            log_exception(logger, "OpenSearch configuration error", e)
            if self.environment == 'lambda':
                # In Lambda, this is a critical error
                raise HTTPException(
                    status_code=500,
                    detail=f"OpenSearch configuration error in Lambda: {str(e)}"
                )
            else:
                # In local/dev, just warn and continue
                logger.warning("Continuing without OpenSearch in development environment")
                return None
        except Exception as e:
            log_exception(logger, "Unexpected error initializing Opensearch client", e)
            if self.environment == 'lambda':
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize OpenSearch in Lambda: {str(e)}"
                )
            return None

    def _test_opensearch_connection(self, opensearch_client: OpenSearch, timeout: int = 30) -> OpenSearch:
        """Test OpenSearch connection with configurable timeout."""
        try:
            logger.info(f"Testing OpenSearch connection with {timeout}s timeout...")
            
            # Use a shorter timeout for the connection test
            test_client = OpenSearch(
                hosts=[{
                    'host': config.OPENSEARCH_HOST,
                    'port': config.OPENSEARCH_PORT
                }],
                http_auth=(config.OPENSEARCH_USER, config.OPENSEARCH_PASSWORD),
                use_ssl=getattr(config, 'OPENSEARCH_USE_SSL', True),
                verify_certs=getattr(config, 'OPENSEARCH_VERIFY_CERTS', True),
                timeout=timeout,
                max_retries=1,
                retry_on_timeout=False
            )
            
            info = test_client.info()
            logger.info(f"OpenSearch connection successful. Cluster info: {info.get('cluster_name', 'Unknown')}")
            return opensearch_client
            
        except OpenSearchException as e:
            log_exception(logger, "OpenSearch connection test failed", e)
            raise OpenSearchConfigurationError(f"Failed to connect to OpenSearch: {str(e)}")
        except (ConnectionError, Timeout) as e:
            log_exception(logger, f"Network error connecting to OpenSearch (timeout: {timeout}s)", e)
            if self.environment == 'local':
                raise OpenSearchConfigurationError(
                    f"OpenSearch unreachable in local environment. "
                    f"This is expected if OpenSearch is in VPC. "
                    f"Set OPENSEARCH_ENABLED=false or FORCE_OPENSEARCH_LOCAL=false for local development."
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail="OpenSearch service is unavailable. Please try again later."
                )

    # Optional: Method to index data to OpenSearch (when enabled)
    async def _index_to_opensearch(self, material_data: MaterialData, id: str) -> None:
        """Index material data to OpenSearch if enabled and available."""
        # Check if OpenSearch is enabled and available
        if not getattr(config, 'OPENSEARCH_ENABLED', True):
            logger.info("OpenSearch indexing disabled via configuration, skipping")
            return
        
        if not self.opensearch_client:
            logger.warning(f"OpenSearch client not available in {self.environment} environment, skipping indexing")
            if self.environment == 'lambda':
                # In Lambda, this might be a critical issue
                error = OpenSearchConfigurationError("OpenSearch client not initialized in production environment")
                log_exception(logger, "OpenSearch client not initialized in Lambda environment", error)
                raise error
            return
        
        try:
            logger.info(f"Indexing material data in OpenSearch with ID: {id}")
            
            index_name = self.config.opensearch_index_name
            if not index_name:
                raise OpenSearchConfigurationError("OPENSEARCH_INDEX_NAME not configured")
            
            response = await self._index_with_retry(index_name, material_data, id)
            logger.info(f"Successfully indexed material data in OpenSearch: {response.get('_id', 'Unknown ID')}")
            
        except Exception as e:
            log_exception(logger, "Failed to index data to OpenSearch", e)
            if self.environment == 'lambda':
                # In production, indexing failure might be critical
                raise HTTPException(
                    status_code=500,
                    detail=f"OpenSearch indexing failed in production: {str(e)}"
                )
            else:
                # In development, just log the error and continue
                logger.warning(f"OpenSearch indexing failed in {self.environment} environment, continuing...")

    @async_retry(max_retries=3, exceptions=(OpenSearchException, ConnectionError, Timeout))
    async def _index_with_retry(self, index_name: str, material_data: MaterialData, id: str) -> Dict:
        """Index data to OpenSearch with retry logic."""
        if not self.opensearch_client:
            raise OpenSearchConfigurationError("OpenSearch client not available")
            
        return self.opensearch_client.index(
            index=index_name,
            body=material_data.model_dump(),
            id=id,
            refresh=True,
            timeout='60s'
        )

    def _validate_file_retrieval_inputs(self, file_names: List[str]) -> None:
        """Validate inputs for file retrieval."""
        if not self.s3_client:
            raise HTTPException(
                status_code=500,
                detail="S3 client not initialized. Check AWS credentials and configuration."
            )
        
        bucket_name = config.S3_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(
                status_code=500, 
                detail="S3 bucket name not configured. Please set AWS_S3_BUCKET_NAME environment variable."
            )

        if not file_names:
            raise HTTPException(
                status_code=400,
                detail="No file names provided"
            )

    def _process_single_file_retrieval(self, filename: str, bucket_name: str) -> Tuple[Optional[BytesIO], Optional[Dict], Optional[Dict]]:
        """Process single file retrieval from S3."""
        try:
            if not filename or not filename.strip():
                return None, None, {"filename": filename, "error": "Empty or invalid filename"}

            # Check file existence and get metadata
            try:
                response = self.s3_client.head_object(Bucket=bucket_name, Key=filename)
                file_size = response['ContentLength']
                content_type = response.get('ContentType', 'application/octet-stream')
                last_modified = response['LastModified']
                
                # Validate file size
                if file_size > self.config.max_file_size_bytes:
                    return None, None, {
                        "filename": filename,
                        "error": f"File size ({file_size} bytes) exceeds maximum allowed size ({self.config.max_file_size_bytes} bytes)"
                    }
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                
                if error_code == '404':
                    error_msg = f"File '{filename}' not found in S3 bucket '{bucket_name}'"
                elif error_code == 'AccessDenied':
                    error_msg = f"Access denied to file '{filename}'"
                else:
                    error_msg = f"S3 error: {error_message}"
                
                return None, None, {"filename": filename, "error": error_msg}

            # Download file
            try:
                file_obj = self.s3_client.get_object(Bucket=bucket_name, Key=filename)
                file_content = file_obj['Body'].read()
                file_stream = BytesIO(file_content)
                
                metadata = {
                    "size_bytes": file_size,
                    "content_type": content_type,
                    "last_modified": last_modified.isoformat(),
                    "actual_size": len(file_content)
                }
                
                logger.info(f"Successfully retrieved {filename} from S3 ({len(file_content)} bytes)")
                return file_stream, metadata, None
                
            except ClientError as e:
                error_message = e.response['Error']['Message']
                return None, None, {"filename": filename, "error": f"Download error: {error_message}"}
                
        except Exception as e:
            log_exception(logger, f"Unexpected error processing file {filename}", e)
            return None, None, {"filename": filename, "error": f"Unexpected error: {str(e)}"}

    def get_files_by_names(self, file_names: List[str]) -> Dict[str, Any]:
        """
        Retrieve multiple files from S3 by their names with comprehensive error handling.
        
        Args:
            file_names: List of file names to retrieve from S3
            
        Returns:
            dict: Dictionary containing file streams and metadata
            
        Raises:
            HTTPException: If S3 client is not initialized or bucket name is not configured
        """
        logger.info(f"Starting file retrieval for {len(file_names)} files: {file_names}")
        
        self._validate_file_retrieval_inputs(file_names)
        bucket_name = config.S3_BUCKET_NAME

        file_streams = {}
        file_metadata = {}
        failed_files = []

        for filename in file_names:
            file_stream, metadata, error = self._process_single_file_retrieval(filename, bucket_name)
            
            if error:
                failed_files.append(error)
            else:
                file_streams[filename] = file_stream
                file_metadata[filename] = metadata

        # Log summary and handle errors
        log_structured(logger, 'INFO', "File retrieval completed",
                      successful_files=len(file_streams),
                      failed_files=len(failed_files),
                      total_files=len(file_names),
                      environment=self.environment)
        
        if failed_files and not file_streams:
            error = HTTPException(
                status_code=404 if any("not found" in f["error"] for f in failed_files) else 500,
                detail={
                    "message": "All files failed to retrieve",
                    "failed_files": failed_files,
                    "total_failed": len(failed_files)
                }
            )
            log_exception(logger, "All files failed to retrieve", error)
            raise error

        return {
            "file_stream": file_streams,
            "file_metadata": file_metadata,
            "failed_files": failed_files if failed_files else None,
            "total_successful": len(file_streams),
            "total_failed": len(failed_files)
        }

    async def vectorize_files(self, file_streams_dict: Dict[str, BytesIO], id: str, category: int) -> VectorizationResponse:
        """
        Process file streams and create embeddings for text chunks with comprehensive error handling.
        
        Args:
            file_streams_dict: Dictionary of filename -> file_stream from S3
            id: Unique identifier for the material
            category: Category number for the material
            
        Returns:
            VectorizationResponse: Dictionary containing processing status and results
            
        Raises:
            HTTPException: If critical errors occur during processing
        """
        start_time = datetime.now()
        logger.info(f"Starting vectorization process for {len(file_streams_dict)} files")
        logger.info(f"Material ID: {id}, Category: {category}")
        
        # Validate inputs
        self._validate_vectorization_inputs(file_streams_dict, id)
        
        # Process files and create embeddings
        file_contents, processing_errors = await self._process_file_contents(file_streams_dict)
        documents, embedding_errors = await self._create_document_embeddings(file_contents)
        material_data = self._prepare_material_data(id, category, documents)
        
        # Index to OpenSearch if available (only fail in production)
        try:
            await self._index_to_opensearch(material_data, id)
        except Exception as e:
            log_exception(logger, "OpenSearch indexing failed", e)
            # Only add to warnings, don't fail the entire process unless in Lambda
            if self.environment == 'lambda':
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
            material_id=id,
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
        log_structured(logger, 'INFO', "Vectorization completed", 
                      material_id=id, 
                      total_documents=len(documents),
                      total_chunks=sum(len(doc.chunks) for doc in documents),
                      processing_time_seconds=f"{processing_time:.3f}",
                      environment=self.environment)
        
        return response

    def _validate_vectorization_inputs(self, file_streams_dict: Dict[str, BytesIO], id: str) -> None:
        """Validate inputs for vectorization."""
        if not file_streams_dict:
            raise HTTPException(
                status_code=400,
                detail="No files provided for vectorization"
            )
        
        if not id or not str(id).strip():
            raise HTTPException(
                status_code=400,
                detail="Valid material ID is required"
            )

    async def _process_file_contents(self, file_streams_dict: Dict[str, BytesIO]) -> Tuple[Dict[str, str], List[Dict]]:
        """Process file streams and extract content."""
        file_contents = {}
        processing_errors = []
        
        # Process files in parallel for better performance
        tasks = []
        for filename, file_stream in file_streams_dict.items():
            task = asyncio.create_task(self._process_single_file_content(filename, file_stream))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            filename = list(file_streams_dict.keys())[i]
            
            if isinstance(result, Exception):
                error_msg = f"Failed to process file {filename}"
                log_exception(logger, error_msg, result)
                processing_errors.append({"filename": filename, "error": f"{error_msg}: {str(result)}"})
            elif result:
                content, error = result
                if error:
                    processing_errors.append({"filename": filename, "error": error})
                else:
                    file_contents[filename] = content
        
        if not file_contents:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "No files could be processed successfully",
                    "processing_errors": processing_errors,
                    "total_files": len(file_streams_dict),
                    "failed_files": len(processing_errors)
                }
            )
        
        logger.info(f"Successfully processed {len(file_contents)} out of {len(file_streams_dict)} files")
        return file_contents, processing_errors

    async def _process_single_file_content(self, filename: str, file_stream: BytesIO) -> Tuple[Optional[str], Optional[str]]:
        """Process a single file and extract its content."""
        try:
            # Reset stream position
            file_stream.seek(0)
            
            # Extension validation
            if '.' not in filename:
                return None, f"File has no extension: {filename}"
            
            extension = filename.split(".")[-1].lower()
            if extension not in self.config.allowed_extensions:
                return None, f"File type not allowed: {filename}. Allowed types: {', '.join(self.config.allowed_extensions)}"

            # Create mock UploadFile object
            class MockUploadFile:
                def __init__(self, file_stream, filename):
                    self.file = file_stream
                    self.filename = filename
            
            mock_file = MockUploadFile(file_stream, filename)
            structured_content = extract_content_with_tags(mock_file, extension)
            
            if not structured_content or not structured_content.strip():
                return None, f"No extractable content found in file: {filename}"
            
            logger.info(f"Successfully extracted content from {filename} ({len(structured_content)} characters)")
            return structured_content, None
            
        except Exception as e:
            log_exception(logger, f"Error processing file {filename}", e)
            return None, f"Failed to extract content from {filename}: {str(e)}"

    async def _create_document_embeddings(self, file_contents: Dict[str, str]) -> Tuple[List[DocumentData], List[Dict]]:
        """Create embeddings for document chunks."""
        documents = []
        embedding_errors = []
        count = 0
        
        for filename, content in file_contents.items():
            try:
                logger.info(f"Creating chunks for {filename}")
                file_chunks = split_into_chunks(content, source_info=filename, max_tokens=self.config.max_tokens_per_chunk)
                
                if not file_chunks:
                    error_msg = f"No chunks generated for file: {filename}"
                    logger.warning(error_msg)
                    embedding_errors.append({"filename": filename, "error": error_msg})
                    continue
                
                chunks = await self._process_chunks_for_embeddings(filename, file_chunks, embedding_errors)
                
                if chunks:
                    documents.append(DocumentData(
                        document_id=count + 1,
                        document_source=filename,
                        chunks=chunks
                    ))
                    count += 1
                    logger.info(f"Successfully created {len(chunks)} embeddings for {filename}")
                else:
                    error_msg = f"No valid chunks with embeddings created for {filename}"
                    fake_error = ValidationError(error_msg)
                    log_exception(logger, error_msg, fake_error)
                    embedding_errors.append({"filename": filename, "error": error_msg})
                    
            except Exception as e:
                error_msg = f"Failed to process chunks for {filename}"
                log_exception(logger, error_msg, e)
                embedding_errors.append({"filename": filename, "error": f"{error_msg}: {str(e)}"})
                continue

        if not documents:
            error = HTTPException(
                status_code=500,
                detail={
                    "message": "Failed to create embeddings for any documents",
                    "embedding_errors": embedding_errors
                }
            )
            log_exception(logger, "No documents with embeddings were created", error)
            raise error
        
        return documents, embedding_errors

    async def _process_chunks_for_embeddings(self, filename: str, file_chunks: List[Dict], embedding_errors: List[Dict]) -> List[ChunkData]:
        """Process chunks and create embeddings with parallel processing."""
        chunks = []
        
        # Create tasks for parallel embedding creation
        tasks = []
        for chunk_idx, chunk in enumerate(file_chunks):
            if not chunk.get("chunk_text") or not chunk["chunk_text"].strip():
                logger.warning(f"Empty chunk {chunk_idx} in {filename}, skipping")
                continue
            
            task = asyncio.create_task(self._create_single_embedding(filename, chunk_idx, chunk))
            tasks.append((chunk_idx, task))
        
        # Process results
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for i, result in enumerate(results):
            chunk_idx, _ = tasks[i]
            
            if isinstance(result, Exception):
                error_msg = f"Failed to create embedding for chunk {chunk_idx} in {filename}"
                log_exception(logger, error_msg, result)
                embedding_errors.append({"filename": filename, "chunk_id": chunk_idx, "error": f"{error_msg}: {str(result)}"})
            elif result:
                chunks.append(result)
        
        return chunks

    @async_retry(max_retries=3, exceptions=(Exception,))
    async def _create_single_embedding(self, filename: str, chunk_idx: int, chunk: Dict) -> ChunkData:
        """Create embedding for a single chunk with retry logic."""
        try:
            logger.info(f"Creating embedding for chunk {chunk_idx} of {filename}")
            response = self.openai_client.embeddings.create(
                input=chunk["chunk_text"],
                model="text-embedding-3-small"
            )
            
            if not response or not response.data or not response.data[0].embedding:
                raise EmbeddingCreationError("Invalid response from OpenAI API")
            
            embedding_data = response.data[0].embedding
            if not embedding_data:
                raise EmbeddingCreationError("Empty embedding returned from OpenAI API")
            
            return ChunkData(
                chunk_id=chunk["chunk_id"],
                embedding=embedding_data,
                chunk_text=chunk["chunk_text"]
            )
            
        except Exception as e:
            error_type = type(e).__name__
            
            # Handle rate limiting
            if "rate" in str(e).lower() or "quota" in str(e).lower() or error_type in ["RateLimitError"]:
                logger.warning(f"Rate limit hit for chunk {chunk_idx} of {filename}: {e}")
                raise
            
            # Handle API errors  
            elif "api" in str(e).lower() or error_type in ["APIError", "AuthenticationError", "PermissionDeniedError"]:
                log_exception(logger, f"OpenAI API error for chunk {chunk_idx} of {filename}", e)
                raise
            
            # Handle other errors
            else:
                log_exception(logger, f"Unexpected error creating embedding for chunk {chunk_idx} of {filename}", e)
                raise

    def _prepare_material_data(self, id: str, category: int, documents: List[DocumentData]) -> MaterialData:
        """Prepare material data for indexing."""
        try:
            material_data = MaterialData(
                id=id,
                category=category,
                documents=documents
            )
            
            total_chunks = sum(len(doc.chunks) for doc in documents)
            logger.info(f"Created MaterialData with {len(documents)} documents and {total_chunks} chunks")
            
            return material_data
            
        except Exception as e:
            log_exception(logger, "Failed to create MaterialData object", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to prepare data for indexing: {str(e)}"
            )

# Environment Detection Utilities
def is_lambda_environment() -> bool:
    """
    Detect if the code is running in AWS Lambda environment.
    
    Returns:
        bool: True if running in Lambda, False otherwise
    """
    # AWS Lambda sets several specific environment variables
    lambda_indicators = [
        'AWS_LAMBDA_FUNCTION_NAME',
        'AWS_LAMBDA_FUNCTION_VERSION', 
        'AWS_LAMBDA_RUNTIME_API',
        'LAMBDA_TASK_ROOT'
    ]
    
    # Check if any Lambda-specific environment variables exist
    for indicator in lambda_indicators:
        if os.environ.get(indicator):
            return True
    
    # Additional check for Lambda execution environment
    if os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_Lambda'):
        return True
        
    return False


def is_local_development() -> bool:
    """
    Detect if the code is running in local development environment.
    
    Returns:
        bool: True if running locally, False otherwise
    """
    # Common local development indicators
    local_indicators = [
        os.environ.get('ENVIRONMENT') in ['local', 'development', 'dev'],
        os.environ.get('ENV') in ['local', 'development', 'dev'],
        os.environ.get('NODE_ENV') == 'development',
        os.path.exists('/.dockerenv'),  # Running in Docker
        not is_lambda_environment(),
    ]
    
    return any(local_indicators)


def get_environment_type() -> str:
    """
    Get the current environment type.
    
    Returns:
        str: Environment type ('lambda', 'local', 'container', 'unknown')
    """
    if is_lambda_environment():
        return 'lambda'
    elif os.path.exists('/.dockerenv'):
        return 'container'
    elif is_local_development():
        return 'local'
    else:
        return 'unknown'