import logging
import traceback
import asyncio
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from openai import OpenAI
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from io import BytesIO
from opensearchpy import OpenSearch, OpenSearchException
from requests.exceptions import RequestException, Timeout, ConnectionError

from services.file_service import extract_content_with_tags
from services.text_service import split_into_chunks
from schemas.vectorize_schemas import ChunkData, DocumentData, MaterialData
from config import config


# Configure logger with more detailed formatting
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FileController:
    def __init__(self):
        """Initialize FileController with proper error handling and logging."""
        logger.info("Initializing FileController...")
        
        # Initialize OpenAI client with validation
        try:
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not configured")
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            logger.info("OpenAI client configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure OpenAI client: {e}")
            raise HTTPException(
                status_code=500,
                detail="OpenAI configuration error. Please check API key configuration."
            )
        
        # Initialize S3 client with comprehensive error handling
        self.s3_client = self._initialize_s3_client()
        
        # Initialize Opensearch client with comprehensive error handling
        # self.opensearch_client = self._initialize_opensearch_client()
        
        logger.info("FileController initialization completed successfully")

    def _initialize_s3_client(self) -> Optional[boto3.client]:
        """Initialize S3 client with proper error handling."""
        try:
            logger.info("Initializing S3 client...")
            
            # Validate required configuration
            if not config.REGION:
                raise ValueError("AWS region is not configured")
            
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
            
            # Test S3 connection
            try:
                s3_client.list_buckets()
                logger.info("S3 client initialized and tested successfully")
                return s3_client
            except ClientError as e:
                error_code = e.response['Error']['Code']
                logger.error(f"S3 connection test failed with error code {error_code}: {e}")
                if error_code in ['InvalidAccessKeyId', 'SignatureDoesNotMatch']:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid AWS credentials. Please check ACCESS_KEY_ID and SECRET_ACCESS_KEY."
                    )
                raise
            except BotoCoreError as e:
                logger.error(f"S3 connection test failed with BotoCore error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="AWS service configuration error. Please check your AWS settings."
                )
                
        except ValueError as e:
            logger.error(f"S3 configuration error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"S3 configuration error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error initializing S3 client: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _initialize_opensearch_client(self) -> Optional[OpenSearch]:
        """Initialize Opensearch client with proper error handling."""
        try:
            logger.info(f"Initializing Opensearch client with host: {config.OPENSEARCH_HOST}")
            
            # Validate required configuration
            required_configs = [
                (config.OPENSEARCH_HOST, "OPENSEARCH_HOST"),
                (config.OPENSEARCH_PORT, "OPENSEARCH_PORT"),
                (config.OPENSEARCH_USER, "OPENSEARCH_USER"),
                (config.OPENSEARCH_PASSWORD, "OPENSEARCH_PASSWORD")
            ]
            
            for config_value, config_name in required_configs:
                if not config_value:
                    raise ValueError(f"{config_name} is not configured")
            
            opensearch_client = OpenSearch(
                hosts=[{
                    'host': config.OPENSEARCH_HOST,
                    'port': config.OPENSEARCH_PORT
                }],
                http_auth=(config.OPENSEARCH_USER, config.OPENSEARCH_PASSWORD),
                use_ssl=config.OPENSEARCH_USE_SSL,
                verify_certs=config.OPENSEARCH_VERIFY_CERTS,
                connection_class=None,
                timeout=60,  # Increased timeout for better reliability
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test the connection with proper error handling
            try:
                info = opensearch_client.info()
                logger.info(f"Opensearch client initialized successfully. Cluster info: {info}")
                return opensearch_client
            except OpenSearchException as e:
                logger.error(f"Opensearch connection test failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to connect to Opensearch: {str(e)}"
                )
            except (ConnectionError, Timeout) as e:
                logger.error(f"Network error connecting to Opensearch: {e}")
                raise HTTPException(
                    status_code=503,
                    detail="Opensearch service is unavailable. Please try again later."
                )
                
        except ValueError as e:
            logger.error(f"Opensearch configuration error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Opensearch configuration error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error initializing Opensearch client: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

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
        
        # Validate S3 client
        if not self.s3_client:
            logger.error("S3 client is not initialized")
            raise HTTPException(
                status_code=500,
                detail="S3 client not initialized. Check AWS credentials and configuration."
            )
        
        # Validate bucket configuration
        bucket_name = config.S3_BUCKET_NAME
        if not bucket_name:
            logger.error("S3 bucket name not configured")
            raise HTTPException(
                status_code=500, 
                detail="S3 bucket name not configured. Please set AWS_S3_BUCKET_NAME environment variable."
            )

        # Validate input
        if not file_names:
            logger.warning("Empty file names list provided")
            raise HTTPException(
                status_code=400,
                detail="No file names provided"
            )

        file_streams = {}
        file_metadata = {}
        failed_files = []

        logger.info(f"Retrieving files from S3 bucket: {bucket_name}")

        for filename in file_names:
            try:
                logger.debug(f"Processing file: {filename}")
                
                if not filename or not filename.strip():
                    failed_files.append({
                        "filename": filename,
                        "error": "Empty or invalid filename"
                    })
                    continue

                # Check if file exists and get metadata
                try:
                    logger.debug(f"Checking existence of file: {filename}")
                    response = self.s3_client.head_object(Bucket=bucket_name, Key=filename)
                    file_size = response['ContentLength']
                    content_type = response.get('ContentType', 'application/octet-stream')
                    last_modified = response['LastModified']
                    
                    logger.info(f"Found file {filename} in S3: size={file_size} bytes, type={content_type}")
                    
                    # Validate file size
                    max_file_size = getattr(config, 'MAX_FILE_SIZE_BYTES', 100 * 1024 * 1024)  # 100MB default
                    if file_size > max_file_size:
                        failed_files.append({
                            "filename": filename,
                            "error": f"File size ({file_size} bytes) exceeds maximum allowed size ({max_file_size} bytes)"
                        })
                        continue
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    error_message = e.response['Error']['Message']
                    
                    if error_code == '404':
                        logger.warning(f"File not found: {filename}")
                        failed_files.append({
                            "filename": filename,
                            "error": f"File '{filename}' not found in S3 bucket '{bucket_name}'"
                        })
                    elif error_code == 'AccessDenied':
                        logger.error(f"Access denied for file: {filename}")
                        failed_files.append({
                            "filename": filename,
                            "error": f"Access denied to file '{filename}'"
                        })
                    else:
                        logger.error(f"S3 error checking file {filename}: {error_code} - {error_message}")
                        failed_files.append({
                            "filename": filename,
                            "error": f"S3 error: {error_message}"
                        })
                    continue
                except BotoCoreError as e:
                    logger.error(f"AWS service error checking file {filename}: {e}")
                    failed_files.append({
                        "filename": filename,
                        "error": f"AWS service error: {str(e)}"
                    })
                    continue

                # Get file object
                try:
                    logger.debug(f"Downloading file: {filename}")
                    file_obj = self.s3_client.get_object(Bucket=bucket_name, Key=filename)
                    file_content = file_obj['Body'].read()
                    file_stream = BytesIO(file_content)
                    
                    file_streams[filename] = file_stream
                    file_metadata[filename] = {
                        "size_bytes": file_size,
                        "content_type": content_type,
                        "last_modified": last_modified.isoformat(),
                        "actual_size": len(file_content)
                    }
                    
                    logger.info(f"Successfully retrieved {filename} from S3 ({len(file_content)} bytes)")
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    error_message = e.response['Error']['Message']
                    logger.error(f"Failed to download file {filename}: {error_code} - {error_message}")
                    failed_files.append({
                        "filename": filename,
                        "error": f"Download error: {error_message}"
                    })
                    continue
                except BotoCoreError as e:
                    logger.error(f"AWS service error downloading file {filename}: {e}")
                    failed_files.append({
                        "filename": filename,
                        "error": f"AWS service error during download: {str(e)}"
                    })
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error processing file {filename}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                failed_files.append({
                    "filename": filename,
                    "error": f"Unexpected error: {str(e)}"
                })
                continue

        # Log summary
        logger.info(f"File retrieval completed. Successful: {len(file_streams)}, Failed: {len(failed_files)}")
        
        if failed_files:
            logger.warning(f"Failed files: {[f['filename'] for f in failed_files]}")

        # Check if all files failed
        if failed_files and not file_streams:
            logger.error("All files failed to retrieve")
            raise HTTPException(
                status_code=404 if any("not found" in f["error"] for f in failed_files) else 500,
                detail={
                    "message": "All files failed to retrieve",
                    "failed_files": failed_files,
                    "total_failed": len(failed_files)
                }
            )

        return {
            "file_stream": file_streams,  # Keep this key for compatibility with router
            "file_metadata": file_metadata,
            "failed_files": failed_files if failed_files else None,
            "total_successful": len(file_streams),
            "total_failed": len(failed_files)
        }

    async def vectorize_files(self, file_streams_dict: Dict[str, BytesIO], id: str, category: int) -> Dict[str, Any]:
        """
        Process file streams and create embeddings for text chunks with comprehensive error handling.
        
        Args:
            file_streams_dict: Dictionary of filename -> file_stream from S3
            id: Unique identifier for the material
            category: Category number for the material
            
        Returns:
            dict: Dictionary containing processing status and results
            
        Raises:
            HTTPException: If critical errors occur during processing
        """
        logger.info(f"Starting vectorization process for {len(file_streams_dict)} files")
        logger.info(f"Material ID: {id}, Category: {category}")
        
        # Validate inputs
        if not file_streams_dict:
            logger.error("No file streams provided for vectorization")
            raise HTTPException(
                status_code=400,
                detail="No files provided for vectorization"
            )
        
        if not id or not str(id).strip():
            logger.error("Invalid material ID provided")
            raise HTTPException(
                status_code=400,
                detail="Valid material ID is required"
            )

        # Validate configuration
        allowed_extensions = getattr(config, 'ALLOWED_FILE_EXTENSIONS', [])
        if not allowed_extensions:
            logger.error("No allowed file extensions configured")
            raise HTTPException(
                status_code=500,
                detail="File processing configuration error: No allowed extensions configured"
            )
        
        max_tokens = getattr(config, 'MAX_TOKENS_PER_CHUNK', 512)
        logger.info(f"Using max tokens per chunk: {max_tokens}")
        
        file_contents = {}
        processing_errors = []

        # Process each file stream with detailed error handling
        for filename, file_stream in file_streams_dict.items():
            try:
                logger.info(f"Processing file: {filename}")
                
                # Reset stream position
                file_stream.seek(0)
                
                # Extension validation
                if '.' not in filename:
                    error_msg = f"File has no extension: {filename}"
                    logger.warning(error_msg)
                    processing_errors.append({"filename": filename, "error": error_msg})
                    continue
                    
                extension = filename.split(".")[-1].lower()
                if extension not in allowed_extensions:
                    error_msg = f"File type not allowed: {filename}. Allowed types: {', '.join(allowed_extensions)}"
                    logger.warning(error_msg)
                    processing_errors.append({"filename": filename, "error": error_msg})
                    continue

                # Create a mock UploadFile object for compatibility with extract_content_with_tags
                class MockUploadFile:
                    def __init__(self, file_stream, filename):
                        self.file = file_stream
                        self.filename = filename
                        
                try:
                    mock_file = MockUploadFile(file_stream, filename)
                    logger.debug(f"Extracting content from {filename}")
                    structured_content = extract_content_with_tags(mock_file, extension)
                    
                    if not structured_content or not structured_content.strip():
                        error_msg = f"No extractable content found in file: {filename}"
                        logger.warning(error_msg)
                        processing_errors.append({"filename": filename, "error": error_msg})
                        continue
                    
                    file_contents[filename] = structured_content
                    logger.info(f"Successfully extracted content from {filename} ({len(structured_content)} characters)")
                    
                except Exception as e:
                    error_msg = f"Failed to extract content from {filename}: {str(e)}"
                    logger.error(error_msg)
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    processing_errors.append({"filename": filename, "error": error_msg})
                    continue
                    
            except Exception as e:
                error_msg = f"Unexpected error processing file {filename}: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                processing_errors.append({"filename": filename, "error": error_msg})
                continue

        # Check if any files were successfully processed
        if not file_contents:
            logger.error("No files were successfully processed")
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

        # Split content into chunks and create embeddings
        documents = []
        embedding_errors = []
        count = 0
        
        for filename, content in file_contents.items():
            try:
                logger.debug(f"Creating chunks for {filename}")
                file_chunks = split_into_chunks(content, source_info=filename, max_tokens=max_tokens)
                
                if not file_chunks:
                    error_msg = f"No chunks generated for file: {filename}"
                    logger.warning(error_msg)
                    embedding_errors.append({"filename": filename, "error": error_msg})
                    continue
                
                chunks = []
                logger.info(f"Processing {len(file_chunks)} chunks for {filename}")

                for chunk_idx, chunk in enumerate(file_chunks):
                    try:
                        # Validate chunk content
                        if not chunk.get("chunk_text") or not chunk["chunk_text"].strip():
                            logger.warning(f"Empty chunk {chunk_idx} in {filename}, skipping")
                            continue
                        
                        # Create embedding with retry logic
                        max_retries = 3
                        embedding_data = None
                        
                        for attempt in range(max_retries):
                            try:
                                logger.debug(f"Creating embedding for chunk {chunk_idx} of {filename} (attempt {attempt + 1})")
                                response = self.openai_client.embeddings.create(
                                    input=chunk["chunk_text"],
                                    model="text-embedding-3-small"
                                )
                                
                                if not response or not response.data or not response.data[0].embedding:
                                    raise ValueError("Invalid response from OpenAI API")
                                
                                embedding_data = response.data[0].embedding
                                if not embedding_data:
                                    raise ValueError("Empty embedding returned from OpenAI API")
                                
                                break  # Success, exit retry loop
                                
                            except Exception as e:
                                error_type = type(e).__name__
                                
                                # Handle rate limiting
                                if "rate" in str(e).lower() or "quota" in str(e).lower() or error_type in ["RateLimitError"]:
                                    logger.warning(f"Rate limit hit for chunk {chunk_idx} of {filename}, attempt {attempt + 1}: {e}")
                                    if attempt == max_retries - 1:
                                        raise
                                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                    continue
                                
                                # Handle API errors  
                                elif "api" in str(e).lower() or error_type in ["APIError", "AuthenticationError", "PermissionDeniedError"]:
                                    logger.error(f"OpenAI API error for chunk {chunk_idx} of {filename}: {e}")
                                    raise
                                
                                # Handle other errors
                                else:
                                    logger.error(f"Unexpected error creating embedding for chunk {chunk_idx} of {filename}: {e}")
                                    if attempt == max_retries - 1:
                                        raise
                                    await asyncio.sleep(1)

                        # Create ChunkData object using the schema
                        chunk_data = ChunkData(
                            chunk_id=chunk["chunk_id"],
                            embedding=embedding_data,
                            chunk_text=chunk["chunk_text"]
                        )
                        chunks.append(chunk_data)
                        
                    except Exception as e:
                        error_msg = f"Failed to create embedding for chunk {chunk_idx} in {filename}: {str(e)}"
                        logger.error(error_msg)
                        embedding_errors.append({"filename": filename, "chunk_id": chunk_idx, "error": error_msg})
                        continue

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
                    logger.error(error_msg)
                    embedding_errors.append({"filename": filename, "error": error_msg})
                    
            except Exception as e:
                error_msg = f"Failed to process chunks for {filename}: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                embedding_errors.append({"filename": filename, "error": error_msg})
                continue

        # Check if any documents were successfully created
        if not documents:
            logger.error("No documents with embeddings were created")
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Failed to create embeddings for any documents",
                    "embedding_errors": embedding_errors,
                    "processing_errors": processing_errors
                }
            )
        
        # Create Opensearch Document
        try:
            material_data = MaterialData(
                id=id,
                category=category,
                documents=documents
            )
            logger.info(f"Created MaterialData with {len(material_data.documents)} documents")
            
            # Calculate total chunks for logging
            total_chunks = sum(len(doc.chunks) for doc in documents)
            logger.info(f"Total chunks to be indexed: {total_chunks}")
            
        except Exception as e:
            logger.error(f"Failed to create MaterialData object: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to prepare data for indexing: {str(e)}"
            )

        # # Index the material data in Opensearch with comprehensive error handling
        # if not self.opensearch_client:
        #     logger.error("Opensearch client not initialized")
        #     raise HTTPException(
        #         status_code=500,
        #         detail="Opensearch client not initialized. Check Opensearch configuration."
        #     )
        
        try:
            logger.info(f"Indexing material data in Opensearch with ID: {id}")
            
            # Validate index configuration
            index_name = getattr(config, 'OPENSEARCH_INDEX_NAME', None)
            if not index_name:
                raise ValueError("OPENSEARCH_INDEX_NAME not configured")
            
            # Attempt to index with timeout and retries
            # max_index_retries = 3
            # for attempt in range(max_index_retries):
            #     try:
            #         response = self.opensearch_client.index(
            #             index=index_name,
            #             body=material_data.model_dump(),
            #             id=id,
            #             refresh=True,
            #             timeout='60s'  # Set explicit timeout
            #         )
            #         logger.info(f"Successfully indexed material data in Opensearch: {response}")
            #         break  # Success, exit retry loop
                    
            #     except OpenSearchException as e:
            #         logger.error(f"Opensearch indexing error (attempt {attempt + 1}): {e}")
            #         if attempt == max_index_retries - 1:
            #             raise HTTPException(
            #                 status_code=500,
            #                 detail=f"Failed to index data in Opensearch after {max_index_retries} attempts: {str(e)}"
            #             )
            #         await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            #     except (ConnectionError, Timeout) as e:
            #         logger.error(f"Network error during indexing (attempt {attempt + 1}): {e}")
            #         if attempt == max_index_retries - 1:
            #             raise HTTPException(
            #                 status_code=503,
            #                 detail="Opensearch service is unavailable for indexing. Please try again later."
            #             )
            #         await asyncio.sleep(2 ** attempt)
                    
        except ValueError as e:
            logger.error(f"Opensearch configuration error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Opensearch configuration error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during Opensearch indexing: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during indexing: {str(e)}"
            )
        
        # Prepare final response
        response_data = {
            "status": 200,
            "message": "Vectorization completed successfully",
            "material_id": id,
            "category": category,
            "total_documents": len(documents),
            "total_chunks": sum(len(doc.chunks) for doc in documents),
            "processed_files": len(file_contents),
            "total_files": len(file_streams_dict)
        }
        
        # Include error information if any occurred
        if processing_errors or embedding_errors:
            response_data["warnings"] = {
                "processing_errors": processing_errors if processing_errors else None,
                "embedding_errors": embedding_errors if embedding_errors else None
            }
        
        logger.info(f"Vectorization process completed successfully for material {id}")
        logger.info(f"Final stats: {response_data}")
        
        return response_data