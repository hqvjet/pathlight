import os
from typing import List


class Config:
    """Configuration settings for the agentic service."""
    
    # Environment Detection
    IS_LAMBDA: bool = bool(os.getenv("LAMBDA_FUNCTION_NAME"))
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # AWS Configuration
    ACCESS_KEY_ID: str = os.getenv("ACCESS_KEY_ID", "")
    SECRET_ACCESS_KEY: str = os.getenv("SECRET_ACCESS_KEY", "")
    REGION: str = os.getenv("REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    
    # CORS Configuration
    # ALLOWED_ORIGINS: List[str] = [
    #     "http://localhost:3000",
    #     "http://localhost:3001", 
    #     "https://your-frontend-domain.com",  # Update with your actual domain
    #     "*"  # Remove this in production for better security
    # ]
    ALLOWED_ORIGINS: List[str] = [
        "*"
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-API-Key"
    ]
    
    # File Processing Configuration
    MAX_TOKENS_PER_CHUNK: int = int(os.getenv("MAX_TOKENS_PER_CHUNK", "500"))
    ALLOWED_FILE_EXTENSIONS: set = {"docx", "pdf", "pptx"}
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))  # 10MB default
    
    # Service Configuration
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Lambda-specific configurations
    LAMBDA_TIMEOUT: int = int(os.getenv("LAMBDA_TIMEOUT", "900"))  # 15 minutes max
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration values."""
        errors = []
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
            
        if not cls.S3_BUCKET_NAME:
            errors.append("S3_BUCKET_NAME is required")
            
        if cls.IS_LAMBDA and not (cls.ACCESS_KEY_ID and cls.SECRET_ACCESS_KEY):
            errors.append("AWS credentials are required for Lambda deployment")
            
        return errors


config = Config()
