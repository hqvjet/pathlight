import os
from typing import List


# Application Settings (non-sensitive, can be committed)
class AppSettings:
    """Non-sensitive application settings."""
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_EXTENSIONS = ["pdf", "docx", "txt", "md", "pptx", "xlsx"]
    MAX_TOKENS_PER_CHUNK = 512
    OPENSEARCH_PORT = 443
    OPENSEARCH_USE_SSL = True
    OPENSEARCH_VERIFY_CERTS = True
    OPENSEARCH_INDEX_NAME = "pathlight_materials"
    OPENSEARCH_TIMEOUT = 60
    EMBEDDING_MODEL = "text-embedding-3-small"
    LOG_LEVEL = "INFO"


class Config:
    """Configuration settings for the agentic service - handles secrets and environment variables."""
    
    def __init__(self):
        # Detect environment
        self.environment = self._detect_environment()
        
        # Environment info
        self.ENVIRONMENT = self.environment
        self.IS_LAMBDA = self.environment == "lambda"
        self.IS_LOCAL = self.environment == "local"
        self.IS_TESTING = os.getenv('TESTING', '').lower() == 'true' or os.getenv('PYTEST_CURRENT_TEST') is not None
        
        # Secrets (from environment variables only)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID", "")
        self.SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY", "")
        self.OPENSEARCH_USER = os.getenv("OPENSEARCH_USERNAME", "")
        self.OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "")
        
        # Infrastructure settings
        self.REGION = os.getenv("REGION", "ap-northeast-1")
        self.S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
        self.OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "")
        
        # Application settings with environment-aware defaults
        self.OPENSEARCH_ENABLED = self._get_opensearch_enabled_default()
        self.FORCE_OPENSEARCH_LOCAL = os.getenv("FORCE_OPENSEARCH_LOCAL", "false").lower() == "true"
        
        # Settings from AppSettings (with possible env overrides)
        self.OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", str(AppSettings.OPENSEARCH_PORT)))
        self.OPENSEARCH_USE_SSL = os.getenv("OPENSEARCH_USE_SSL", str(AppSettings.OPENSEARCH_USE_SSL)).lower() == "true"
        self.OPENSEARCH_VERIFY_CERTS = os.getenv("OPENSEARCH_VERIFY_CERTS", str(AppSettings.OPENSEARCH_VERIFY_CERTS)).lower() == "true"
        self.OPENSEARCH_INDEX_NAME = os.getenv("OPENSEARCH_INDEX_NAME", AppSettings.OPENSEARCH_INDEX_NAME)
        self.OPENSEARCH_TIMEOUT = int(os.getenv("OPENSEARCH_TIMEOUT", str(AppSettings.OPENSEARCH_TIMEOUT)))
        
        # File processing settings
        self.MAX_TOKENS_PER_CHUNK = int(os.getenv("MAX_TOKENS_PER_CHUNK", str(AppSettings.MAX_TOKENS_PER_CHUNK)))
        self.ALLOWED_FILE_EXTENSIONS = AppSettings.ALLOWED_FILE_EXTENSIONS
        self.MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", str(AppSettings.MAX_FILE_SIZE_BYTES)))
        
        # Other settings
        self.EMBEDDING_MODEL = AppSettings.EMBEDDING_MODEL
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", AppSettings.LOG_LEVEL)
        self.SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
        
        # CORS Configuration
        self.ALLOWED_ORIGINS = ["*"]
        self.ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.ALLOWED_HEADERS = [
            "Accept", "Accept-Language", "Content-Language", "Content-Type",
            "Authorization", "X-Requested-With", "X-API-Key"
        ]
    
    def _detect_environment(self) -> str:
        """Detect the current environment."""
        # Check explicit environment variable first
        env = os.getenv("ENVIRONMENT", "").lower()
        if env:
            return env
            
        # Auto-detect based on system indicators
        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            return "lambda"
        elif os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING", "").lower() == "true":
            return "testing"
        elif os.path.exists("/.dockerenv"):
            return "container"
        else:
            return "local"
    
    def _get_opensearch_enabled_default(self) -> bool:
        """Get default OpenSearch enabled setting based on environment."""
        env_value = os.getenv("OPENSEARCH_ENABLED", "").lower()
        if env_value:
            return env_value == "true"
            
        # Environment-based defaults
        if self.environment in ['production', 'lambda']:
            return True
        return False
    
    def validate_config(self) -> List[str]:
        """Validate critical configuration values."""
        errors = []
        
        # Critical secrets validation
        if not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
            
        if not self.S3_BUCKET_NAME:
            errors.append("S3_BUCKET_NAME is required")
        
        # OpenSearch validation (only if enabled)
        if self.OPENSEARCH_ENABLED:
            if not self.OPENSEARCH_HOST:
                errors.append("OPENSEARCH_HOST is required when OpenSearch is enabled")
            if not self.OPENSEARCH_USER:
                errors.append("OPENSEARCH_USERNAME is required when OpenSearch is enabled")
            if not self.OPENSEARCH_PASSWORD:
                errors.append("OPENSEARCH_PASSWORD is required when OpenSearch is enabled")
        
        # Lambda-specific validation
        if self.IS_LAMBDA:
            if not (self.ACCESS_KEY_ID and self.SECRET_ACCESS_KEY):
                errors.append("AWS credentials are required for Lambda deployment")
            if not self.OPENSEARCH_ENABLED:
                errors.append("OpenSearch should be enabled in Lambda environment")
                
        return errors
    
    def log_config_summary(self) -> None:
        """Log configuration summary (without secrets)."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=== Configuration Summary ===")
        logger.info(f"Environment: {self.ENVIRONMENT}")
        logger.info(f"OpenSearch Enabled: {self.OPENSEARCH_ENABLED}")
        logger.info(f"OpenSearch Host: {self.OPENSEARCH_HOST if self.OPENSEARCH_HOST else 'Not configured'}")
        logger.info(f"S3 Bucket: {self.S3_BUCKET_NAME if self.S3_BUCKET_NAME else 'Not configured'}")
        logger.info(f"Max File Size: {self.MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB")
        logger.info(f"Allowed Extensions: {', '.join(self.ALLOWED_FILE_EXTENSIONS)}")
        logger.info(f"Is Lambda: {self.IS_LAMBDA}")
        logger.info(f"Is Testing: {self.IS_TESTING}")
        logger.info("=============================")


# Create global config instance
config = Config()
