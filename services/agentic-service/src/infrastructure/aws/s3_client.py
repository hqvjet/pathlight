"""
🪣 S3 Client Manager

Elegant S3 operations with proper error handling and connection management.
Makes S3 operations feel effortless and reliable.
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from io import BytesIO
from typing import Dict, Any, Optional, Tuple, List
from fastapi import HTTPException

from core.logging import setup_logger, log_exception, log_structured
from core.exceptions import S3ConfigurationError, S3OperationError
from core.environment import get_environment_type


logger = setup_logger(__name__)


class S3Client:
    """Professional S3 client with comprehensive error handling."""
    
    def __init__(self, region: str, access_key_id: str = None, secret_access_key: str = None):
        """
        Initialize S3 client with proper error handling.
        
        Args:
            region: AWS region
            access_key_id: Optional AWS access key
            secret_access_key: Optional AWS secret key
        """
        self.environment = get_environment_type()
        self.region = region
        self.client = self._initialize_client(access_key_id, secret_access_key)
        
    def _initialize_client(self, access_key_id: str, secret_access_key: str) -> boto3.client:
        """Initialize S3 client with proper configuration."""
        try:
            logger.info("Initializing S3 client...")
            
            if not self.region:
                raise S3ConfigurationError("AWS region is not configured")
            
            if access_key_id and secret_access_key:
                logger.info("Using provided AWS credentials")
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    region_name=self.region
                )
            else:
                logger.info("Using default AWS credentials (IAM role, etc.)")
                s3_client = boto3.client('s3', region_name=self.region)
            
            self._test_connection(s3_client)
            logger.info("S3 client initialized successfully")
            return s3_client
                
        except S3ConfigurationError:
            raise
        except Exception as e:
            log_exception(logger, "Unexpected error initializing S3 client", e)
            raise S3ConfigurationError(f"Failed to initialize S3 client: {str(e)}")

    def _test_connection(self, s3_client: boto3.client) -> None:
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

    def get_file_metadata(self, bucket_name: str, filename: str) -> Dict[str, Any]:
        """
        Get file metadata from S3.
        
        Args:
            bucket_name: S3 bucket name
            filename: File key in S3
            
        Returns:
            File metadata dictionary
            
        Raises:
            S3OperationError: If operation fails
        """
        try:
            response = self.client.head_object(Bucket=bucket_name, Key=filename)
            return {
                'size_bytes': response['ContentLength'],
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'last_modified': response['LastModified'],
                'etag': response.get('ETag', '')
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise S3OperationError(f"File '{filename}' not found in bucket '{bucket_name}'")
            elif error_code == 'AccessDenied':
                raise S3OperationError(f"Access denied to file '{filename}'")
            else:
                raise S3OperationError(f"S3 error: {e.response['Error']['Message']}")

    def download_file(self, bucket_name: str, filename: str) -> BytesIO:
        """
        Download file from S3.
        
        Args:
            bucket_name: S3 bucket name
            filename: File key in S3
            
        Returns:
            File content as BytesIO stream
            
        Raises:
            S3OperationError: If download fails
        """
        try:
            file_obj = self.client.get_object(Bucket=bucket_name, Key=filename)
            file_content = file_obj['Body'].read()
            return BytesIO(file_content)
        except ClientError as e:
            error_message = e.response['Error']['Message']
            raise S3OperationError(f"Download error for '{filename}': {error_message}")

    def get_file_safely(self, bucket_name: str, filename: str, max_size_bytes: int) -> Tuple[Optional[BytesIO], Optional[Dict], Optional[str]]:
        """
        Safely retrieve a file with size validation and error handling.
        
        Args:
            bucket_name: S3 bucket name
            filename: File key in S3
            max_size_bytes: Maximum allowed file size
            
        Returns:
            Tuple of (file_stream, metadata, error_message)
        """
        try:
            if not filename or not filename.strip():
                return None, None, "Empty or invalid filename"

            # Get metadata first
            try:
                metadata = self.get_file_metadata(bucket_name, filename)
                
                # Validate file size
                if metadata['size_bytes'] > max_size_bytes:
                    return None, None, (
                        f"File size ({metadata['size_bytes']} bytes) exceeds "
                        f"maximum allowed size ({max_size_bytes} bytes)"
                    )
                
            except S3OperationError as e:
                return None, None, str(e)

            # Download file
            try:
                file_stream = self.download_file(bucket_name, filename)
                
                # Update metadata with actual size
                metadata['actual_size'] = len(file_stream.getvalue())
                metadata['last_modified'] = metadata['last_modified'].isoformat()
                
                logger.info(f"Successfully retrieved {filename} from S3 ({metadata['actual_size']} bytes)")
                return file_stream, metadata, None
                
            except S3OperationError as e:
                return None, None, str(e)
                
        except Exception as e:
            log_exception(logger, f"Unexpected error processing file {filename}", e)
            return None, None, f"Unexpected error: {str(e)}"

    def get_multiple_files(self, bucket_name: str, filenames: List[str], max_size_bytes: int) -> Dict[str, Any]:
        """
        Retrieve multiple files from S3 with comprehensive error handling.
        
        Args:
            bucket_name: S3 bucket name
            filenames: List of file keys to retrieve
            max_size_bytes: Maximum allowed file size per file
            
        Returns:
            Dictionary containing file streams, metadata, and any errors
        """
        file_streams = {}
        file_metadata = {}
        failed_files = []

        for filename in filenames:
            file_stream, metadata, error = self.get_file_safely(bucket_name, filename, max_size_bytes)
            
            if error:
                failed_files.append({"filename": filename, "error": error})
            else:
                file_streams[filename] = file_stream
                file_metadata[filename] = metadata

        # Log summary
        log_structured(
            logger, 'INFO', "File retrieval completed",
            successful_files=len(file_streams),
            failed_files=len(failed_files),
            total_files=len(filenames),
            environment=self.environment
        )

        return {
            "file_streams": file_streams,
            "file_metadata": file_metadata,
            "failed_files": failed_files if failed_files else None,
            "total_successful": len(file_streams),
            "total_failed": len(failed_files)
        }
