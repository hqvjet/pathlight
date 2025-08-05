"""
🤖 OpenAI Client Manager

Clean, simple OpenAI client with proper error handling.
Makes AI operations feel natural and reliable.
"""

import openai
from typing import List
from fastapi import HTTPException

from core.logging import setup_logger, log_exception
from core.exceptions import OpenAIConfigurationError, EmbeddingCreationError
from core.retry import async_retry


logger = setup_logger(__name__)


class OpenAIClient:
    """Professional OpenAI client with comprehensive error handling."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model to use
        """
        self.model = model
        self.client = self._initialize_client(api_key)
        
    def _initialize_client(self, api_key: str) -> openai.OpenAI:
        """Initialize OpenAI client with validation."""
        try:
            if not api_key:
                raise OpenAIConfigurationError("OpenAI API key is not configured")
            
            client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client configured successfully")
            return client
            
        except Exception as e:
            log_exception(logger, "Failed to configure OpenAI client", e)
            raise HTTPException(
                status_code=500,
                detail="OpenAI configuration error. Please check API key configuration."
            )

    @async_retry(max_retries=3, exceptions=(Exception,))
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text with retry logic.
        
        Args:
            text: Text to create embedding for
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingCreationError: If embedding creation fails
        """
        try:
            logger.debug(f"Creating embedding for text (length: {len(text)})")
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            
            if not response or not response.data or not response.data[0].embedding:
                raise EmbeddingCreationError("Invalid response from OpenAI API")
            
            embedding_data = response.data[0].embedding
            if not embedding_data:
                raise EmbeddingCreationError("Empty embedding returned from OpenAI API")
            
            return embedding_data
            
        except Exception as e:
            error_type = type(e).__name__
            
            # Handle rate limiting
            if "rate" in str(e).lower() or "quota" in str(e).lower() or error_type in ["RateLimitError"]:
                logger.warning(f"Rate limit hit: {e}")
                raise
            
            # Handle API errors  
            elif "api" in str(e).lower() or error_type in ["APIError", "AuthenticationError", "PermissionDeniedError"]:
                log_exception(logger, "OpenAI API error", e)
                raise
            
            # Handle other errors
            else:
                log_exception(logger, "Unexpected error creating embedding", e)
                raise
