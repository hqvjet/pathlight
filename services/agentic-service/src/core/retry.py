"""
🔄 Retry Utilities for Agentic Service

Elegant retry decorators with exponential backoff.
Because sometimes the first try isn't the charm.
"""

import asyncio
import functools
from typing import Tuple, Callable, Any
from core.logging import setup_logger

logger = setup_logger(__name__)


def async_retry(
    max_retries: int = 3,
    exceptions: Tuple[type, ...] = (Exception,),
    backoff_factor: float = 2.0,
    base_delay: float = 1.0
):
    """
    Retry decorator for async functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        exceptions: Tuple of exceptions to retry on
        backoff_factor: Multiplier for delay between retries
        base_delay: Initial delay in seconds
        
    Returns:
        Decorated function with retry logic
    """
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
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
            return None
        return wrapper
    return decorator
