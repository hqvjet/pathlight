"""
Common environment configuration for Pathlight services.
This module provides a centralized way to load environment variables from the project's .env file.
"""

# Import the new config system and legacy compatibility functions
from .config import (
    Config, 
    config,
    get_database_url, 
    get_debug_mode, 
    get_jwt_config, 
    get_service_port,
    get_service_url,
    is_development,
    is_debug,
    load_env_from_root
)

# Legacy function alias for backward compatibility
def load_pathlight_env():
    """
    Legacy function - use load_env_from_root() instead.
    Load environment variables from the Pathlight project's .env file.
    
    Returns:
        bool: True if .env file was loaded successfully, False otherwise
    """
    return load_env_from_root()

# Auto-load environment on import
load_pathlight_env()
