"""
📁 File Processing Configuration

Clean, organized configuration for file processing operations.
Everything you need to know about file handling in one place.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class FileProcessingConfig:
    """Configuration for file processing operations."""
    
    # File size limits
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB
    
    # Allowed file extensions
    allowed_extensions: List[str] = None
    
    # Text processing
    max_tokens_per_chunk: int = 512
    
    # OpenSearch configuration
    opensearch_index_name: str = None
    
    # Retry configuration
    max_retries: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    
    def __post_init__(self):
        """Post-initialization validation and defaults."""
        if self.allowed_extensions is None:
            self.allowed_extensions = ['pdf', 'docx', 'txt', 'md', 'pptx', 'xlsx']
        
        if self.opensearch_index_name is None:
            self.opensearch_index_name = 'pathlight-materials'
        
        self._validate_config()

    def _validate_config(self):
        """Validate configuration values."""
        if not self.allowed_extensions:
            raise ValueError("allowed_extensions cannot be empty")
        
        if self.max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be positive")
        
        if self.max_tokens_per_chunk <= 0:
            raise ValueError("max_tokens_per_chunk must be positive")
        
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")

    @classmethod
    def from_app_config(cls, app_config) -> 'FileProcessingConfig':
        """
        Create FileProcessingConfig from main app configuration.
        
        Args:
            app_config: Main application configuration object
            
        Returns:
            FileProcessingConfig instance
        """
        return cls(
            max_file_size_bytes=getattr(app_config, 'MAX_FILE_SIZE_BYTES', 100 * 1024 * 1024),
            allowed_extensions=getattr(app_config, 'ALLOWED_FILE_EXTENSIONS', None),
            max_tokens_per_chunk=getattr(app_config, 'MAX_TOKENS_PER_CHUNK', 512),
            opensearch_index_name=getattr(app_config, 'OPENSEARCH_INDEX_NAME', None),
            max_retries=3,
            base_delay=1.0,
            backoff_factor=2.0
        )
