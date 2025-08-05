"""
📄 File Processing Service

Elegant file processing with proper content extraction and validation.
Transforms messy files into clean, structured content.
"""

import asyncio
from io import BytesIO
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from core.logging import setup_logger, log_exception
from core.exceptions import FileProcessingError, ContentExtractionError, FileValidationError
from services.file_service import extract_content_with_tags


logger = setup_logger(__name__)


@dataclass
class ProcessedFile:
    """Result of file processing operation."""
    filename: str
    content: str
    success: bool
    error: Optional[str] = None
    content_length: Optional[int] = None


class FileProcessor:
    """Professional file processor with validation and error handling."""
    
    def __init__(self, allowed_extensions: List[str]):
        """
        Initialize file processor.
        
        Args:
            allowed_extensions: List of allowed file extensions
        """
        self.allowed_extensions = allowed_extensions

    def validate_file_extension(self, filename: str) -> str:
        """
        Validate file extension.
        
        Args:
            filename: File name to validate
            
        Returns:
            File extension (lowercase)
            
        Raises:
            FileValidationError: If extension is not allowed
        """
        if '.' not in filename:
            raise FileValidationError(f"File has no extension: {filename}")
        
        extension = filename.split(".")[-1].lower()
        if extension not in self.allowed_extensions:
            raise FileValidationError(
                f"File type not allowed: {filename}. "
                f"Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        return extension

    async def process_single_file(self, filename: str, file_stream: BytesIO) -> ProcessedFile:
        """
        Process a single file and extract its content.
        
        Args:
            filename: Name of the file
            file_stream: File content stream
            
        Returns:
            ProcessedFile result
        """
        try:
            # Reset stream position
            file_stream.seek(0)
            
            # Validate extension
            extension = self.validate_file_extension(filename)

            # Create mock UploadFile object for compatibility
            class MockUploadFile:
                def __init__(self, file_stream, filename):
                    self.file = file_stream
                    self.filename = filename
            
            mock_file = MockUploadFile(file_stream, filename)
            structured_content = extract_content_with_tags(mock_file, extension)
            
            if not structured_content or not structured_content.strip():
                return ProcessedFile(
                    filename=filename,
                    content="",
                    success=False,
                    error=f"No extractable content found in file: {filename}"
                )
            
            logger.info(f"Successfully extracted content from {filename} ({len(structured_content)} characters)")
            return ProcessedFile(
                filename=filename,
                content=structured_content,
                success=True,
                content_length=len(structured_content)
            )
            
        except FileValidationError as e:
            return ProcessedFile(
                filename=filename,
                content="",
                success=False,
                error=str(e)
            )
        except Exception as e:
            log_exception(logger, f"Error processing file {filename}", e)
            return ProcessedFile(
                filename=filename,
                content="",
                success=False,
                error=f"Failed to extract content: {str(e)}"
            )

    async def process_multiple_files(self, file_streams_dict: Dict[str, BytesIO]) -> Tuple[Dict[str, str], List[Dict]]:
        """
        Process multiple files in parallel.
        
        Args:
            file_streams_dict: Dictionary of filename -> file_stream
            
        Returns:
            Tuple of (successful_files_content, processing_errors)
            
        Raises:
            FileProcessingError: If no files could be processed
        """
        file_contents = {}
        processing_errors = []
        
        # Process files in parallel for better performance
        tasks = []
        for filename, file_stream in file_streams_dict.items():
            task = asyncio.create_task(self.process_single_file(filename, file_stream))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            filename = list(file_streams_dict.keys())[i]
            
            if isinstance(result, Exception):
                error_msg = f"Failed to process file {filename}"
                log_exception(logger, error_msg, result)
                processing_errors.append({"filename": filename, "error": f"{error_msg}: {str(result)}"})
            elif isinstance(result, ProcessedFile):
                if result.success:
                    file_contents[filename] = result.content
                else:
                    processing_errors.append({"filename": filename, "error": result.error})
            else:
                processing_errors.append({"filename": filename, "error": "Unknown processing error"})
        
        if not file_contents:
            raise FileProcessingError(
                f"No files could be processed successfully. "
                f"Errors: {processing_errors}"
            )
        
        logger.info(f"Successfully processed {len(file_contents)} out of {len(file_streams_dict)} files")
        return file_contents, processing_errors
