"""
🚨 Core Exception Classes

Custom exception hierarchy for the agentic service.
Provides clear, structured error handling across all components.
"""

from typing import Optional, Any, Dict


class AgenticServiceError(Exception):
    """Base exception class for all agentic service errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize base exception.
        
        Args:
            message: Human-readable error message
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


# =============================================================================
# Validation Errors
# =============================================================================

class ValidationError(AgenticServiceError):
    """Raised when input validation fails."""
    pass


class FileValidationError(ValidationError):
    """Raised when file validation fails (e.g., invalid extension, format)."""
    pass


# =============================================================================
# Processing Errors
# =============================================================================

class ProcessingError(AgenticServiceError):
    """Raised when data processing operations fail."""
    pass


class FileProcessingError(ProcessingError):
    """Raised when file processing operations fail."""
    pass


class ContentExtractionError(ProcessingError):
    """Raised when content extraction from files fails."""
    pass


class EmbeddingCreationError(ProcessingError):
    """Raised when embedding creation fails."""
    pass


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(AgenticServiceError):
    """Base class for configuration-related errors."""
    pass


class OpenAIConfigurationError(ConfigurationError):
    """Raised when OpenAI client configuration fails."""
    pass


class S3ConfigurationError(ConfigurationError):
    """Raised when S3 client configuration fails."""
    pass


class OpenSearchConfigurationError(ConfigurationError):
    """Raised when OpenSearch client configuration fails."""
    pass


# =============================================================================
# Operation Errors
# =============================================================================

class OperationError(AgenticServiceError):
    """Base class for operation-related errors."""
    pass


class S3OperationError(OperationError):
    """Raised when S3 operations fail."""
    pass


class OpenSearchOperationError(OperationError):
    """Raised when OpenSearch operations fail."""
    pass


# =============================================================================
# HTTP-Related Errors
# =============================================================================

class HTTPError(AgenticServiceError):
    """Base class for HTTP-related errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        """
        Initialize HTTP error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Optional additional details
        """
        super().__init__(message, details)
        self.status_code = status_code


class BadRequestError(HTTPError):
    """Raised for HTTP 400 Bad Request errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)


class UnauthorizedError(HTTPError):
    """Raised for HTTP 401 Unauthorized errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, details)


class ForbiddenError(HTTPError):
    """Raised for HTTP 403 Forbidden errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 403, details)


class NotFoundError(HTTPError):
    """Raised for HTTP 404 Not Found errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, details)


class InternalServerError(HTTPError):
    """Raised for HTTP 500 Internal Server Error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, details)


# =============================================================================
# Utility Functions
# =============================================================================

def create_error_response(error: AgenticServiceError, include_details: bool = False) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.
    
    Args:
        error: The exception to convert
        include_details: Whether to include error details in response
        
    Returns:
        Dictionary with error information
    """
    response = {
        "error": True,
        "message": str(error),
        "type": error.__class__.__name__
    }
    
    if include_details and hasattr(error, 'details') and error.details:
        response["details"] = error.details
    
    if isinstance(error, HTTPError):
        response["status_code"] = error.status_code
    
    return response


def get_error_status_code(error: Exception) -> int:
    """
    Get appropriate HTTP status code for an exception.
    
    Args:
        error: The exception to analyze
        
    Returns:
        HTTP status code
    """
    if isinstance(error, HTTPError):
        return error.status_code
    elif isinstance(error, ValidationError):
        return 400
    elif isinstance(error, ConfigurationError):
        return 500
    elif isinstance(error, OperationError):
        return 500
    else:
        return 500


# =============================================================================
# Exception Mapping
# =============================================================================

# Map exception types to HTTP status codes for consistency
EXCEPTION_STATUS_CODES = {
    ValidationError: 400,
    FileValidationError: 400,
    BadRequestError: 400,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    NotFoundError: 404,
    ProcessingError: 500,
    FileProcessingError: 500,
    ContentExtractionError: 500,
    EmbeddingCreationError: 500,
    ConfigurationError: 500,
    OpenAIConfigurationError: 500,
    S3ConfigurationError: 500,
    OpenSearchConfigurationError: 500,
    OperationError: 500,
    S3OperationError: 500,
    OpenSearchOperationError: 500,
    InternalServerError: 500,
}
