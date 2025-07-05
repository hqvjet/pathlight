import logging
from fastapi import HTTPException
from typing import List
import openai
import boto3
from botocore.exceptions import ClientError
from io import BytesIO

from services.file_service import extract_content_with_tags
from services.text_service import split_into_chunks
from config import config


logger = logging.getLogger(__name__)


class FileController:
    def __init__(self):
        # Initialize OpenAI API key
        openai.api_key = config.OPENAI_API_KEY
        
        # Initialize S3 client with proper error handling
        try:
            if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                    region_name=config.AWS_REGION
                )
            else:
                # Use default AWS credentials (IAM role, etc.)
                self.s3_client = boto3.client('s3', region_name=config.AWS_REGION)
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None

    def get_files_by_names(self, file_names: List[str]):
        """
        Retrieve multiple files from S3 by their names.
        
        Args:
            file_names: List of file names to retrieve from S3
            
        Returns:
            dict: Dictionary containing file streams and metadata
        """
        if not self.s3_client:
            raise HTTPException(
                status_code=500,
                detail="S3 client not initialized. Check AWS credentials."
            )
            
        bucket_name = config.AWS_S3_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(
                status_code=500, 
                detail="S3 bucket name not configured. Please set AWS_S3_BUCKET_NAME environment variable."
            )

        file_streams = {}
        file_metadata = {}
        failed_files = []

        for filename in file_names:
            try:
                # Check if file exists and get metadata
                try:
                    response = self.s3_client.head_object(Bucket=bucket_name, Key=filename)
                    file_size = response['ContentLength']
                    content_type = response.get('ContentType', 'application/octet-stream')
                    last_modified = response['LastModified']
                    
                    logger.info(f"Found file {filename} in S3: size={file_size}, type={content_type}")
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        failed_files.append({
                            "filename": filename,
                            "error": f"File '{filename}' not found in S3 bucket '{bucket_name}'"
                        })
                        continue
                    else:
                        failed_files.append({
                            "filename": filename,
                            "error": f"Error checking file existence: {e.response['Error']['Message']}"
                        })
                        continue

                # Get file object
                try:
                    file_obj = self.s3_client.get_object(Bucket=bucket_name, Key=filename)
                    file_stream = BytesIO(file_obj['Body'].read())
                    
                    file_streams[filename] = file_stream
                    file_metadata[filename] = {
                        "size_bytes": file_size,
                        "content_type": content_type,
                        "last_modified": last_modified.isoformat()
                    }
                    
                    logger.info(f"Successfully retrieved {filename} from S3")
                    
                except ClientError as e:
                    failed_files.append({
                        "filename": filename,
                        "error": f"Error retrieving file: {e.response['Error']['Message']}"
                    })
                    continue
                    
            except Exception as e:
                failed_files.append({
                    "filename": filename,
                    "error": f"Unexpected error: {str(e)}"
                })
                continue

        if failed_files and not file_streams:
            raise HTTPException(
                status_code=404,
                detail=f"All files failed to retrieve: {failed_files}"
            )

        return {
            "file_stream": file_streams,  # Keep this key for compatibility with router
            "file_metadata": file_metadata,
            "failed_files": failed_files if failed_files else None,
            "total_successful": len(file_streams),
            "total_failed": len(failed_files)
        }

    async def vectorize_files(self, file_streams_dict):
        """
        Process file streams and create embeddings for text chunks.
        
        Args:
            file_streams_dict: Dictionary of filename -> file_stream from S3
            
        Returns:
            dict: Dictionary containing embeddings for all file chunks
        """
        allowed_extensions = config.ALLOWED_FILE_EXTENSIONS
        file_contents = {}
        
        logger.info(f"Processing {len(file_streams_dict)} files for vectorization from S3")

        # Process each file stream
        for filename, file_stream in file_streams_dict.items():
            logger.info(f"Processing file: {filename}")
            # Extension validation
            extension = filename.split(".")[-1].lower()
            if extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type not allowed: {filename}. Allowed types: {', '.join(allowed_extensions)}"
                )

            try:
                # Create a mock UploadFile object for compatibility with extract_content_with_tags
                class MockUploadFile:
                    def __init__(self, file_stream, filename):
                        self.file = file_stream
                        self.filename = filename
                        
                mock_file = MockUploadFile(file_stream, filename)
                structured_content = extract_content_with_tags(mock_file, extension)
                file_contents[filename] = structured_content
                logger.info(f"Successfully extracted content from {filename}")
            except Exception as e:
                logger.error(f"Failed to extract content from {filename}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process file {filename}: {str(e)}"
                )

        # Split content into chunks
        chunks = []
        for filename, content in file_contents.items():
            file_chunks = split_into_chunks(content, source_info=filename, max_tokens=config.MAX_TOKENS_PER_CHUNK)
            chunks.extend(file_chunks)
            logger.info(f"Created {len(file_chunks)} chunks from {filename}")

        # Create embeddings for each chunk
        embeddings = []
        for i, chunk in enumerate(chunks):
            try:
                response = openai.Embedding.create(
                    input=chunk["chunk_text"],
                    model="text-embedding-3-small"
                )
                embeddings.append({
                    "chunk_id": chunk["chunk_id"],
                    "embedding": response["data"][0]["embedding"],
                    "chunk_text": chunk["chunk_text"],
                    "source_info": chunk["source_info"],
                    "approx_token_count": chunk.get("approx_token_count", 0)
                })
                    
            except Exception as e:
                logger.error(f"Failed to create embedding for chunk {chunk['chunk_id']}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create embedding for chunk {chunk['chunk_id']}: {str(e)}"
                )

        logger.info(f"Successfully created {len(embeddings)} embeddings")
        return {
            "embeddings": embeddings,
            "total_chunks": len(embeddings),
            "files_processed": len(file_contents)
        }