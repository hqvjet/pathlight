"""
🔧 Logging Utilities for Agentic Service

Provides centralized, environment-aware logging functionality.
Clean, simple, and reusable across the entire application.
"""

import logging
import os
from typing import Dict, Any


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with proper formatting for different environments.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Check if we're in Lambda environment
        is_lambda = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
        
        handler = logging.StreamHandler()
        
        if is_lambda:
            # Lambda-friendly format (single line with escaped newlines)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            # Local development format (multi-line friendly)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    
    return logger


def log_exception(logger_instance: logging.Logger, message: str, exception: Exception) -> None:
    """
    Simple single-line exception logging for all environments.
    
    Args:
        logger_instance: Logger to use
        message: Context message
        exception: Exception to log
    """
    # Always use single line format to avoid Lambda log splitting
    logger_instance.error(f"{message}: {type(exception).__name__}: {str(exception)}")


def log_structured(logger_instance: logging.Logger, level: str, message: str, **kwargs) -> None:
    """
    Simple structured logging for all environments.
    
    Args:
        logger_instance: Logger to use
        level: Log level (info, warning, error, etc.)
        message: Main message
        **kwargs: Additional structured data
    """
    # Simple single-line structured log
    log_parts = [message]
    for key, value in kwargs.items():
        log_parts.append(f"{key}={value}")
    
    log_line = " | ".join(log_parts)
    getattr(logger_instance, level.lower())(log_line)
