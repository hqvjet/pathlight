"""
🌍 Environment Detection Utilities

Smart environment detection for different deployment scenarios.
Knows where it's running and adapts accordingly.
"""

import os


def is_lambda_environment() -> bool:
    """
    Detect if the code is running in AWS Lambda environment.
    
    Returns:
        True if running in Lambda, False otherwise
    """
    # AWS Lambda sets several specific environment variables
    lambda_indicators = [
        'AWS_LAMBDA_FUNCTION_NAME',
        'AWS_LAMBDA_FUNCTION_VERSION', 
        'AWS_LAMBDA_RUNTIME_API',
        'LAMBDA_TASK_ROOT'
    ]
    
    # Check if any Lambda-specific environment variables exist
    for indicator in lambda_indicators:
        if os.environ.get(indicator):
            return True
    
    # Additional check for Lambda execution environment
    if os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_Lambda'):
        return True
        
    return False


def is_local_development() -> bool:
    """
    Detect if the code is running in local development environment.
    
    Returns:
        True if running locally, False otherwise
    """
    # Common local development indicators
    local_indicators = [
        os.environ.get('ENVIRONMENT') in ['local', 'development', 'dev'],
        os.environ.get('ENV') in ['local', 'development', 'dev'],
        os.environ.get('NODE_ENV') == 'development',
        os.path.exists('/.dockerenv'),  # Running in Docker
        not is_lambda_environment(),
    ]
    
    return any(local_indicators)


def is_testing_environment() -> bool:
    """
    Detect if the code is running in a test environment.
    
    Returns:
        True if running tests, False otherwise
    """
    return (
        os.environ.get('PYTEST_CURRENT_TEST') is not None or 
        os.environ.get('TESTING', '').lower() == 'true'
    )


def get_environment_type() -> str:
    """
    Get the current environment type.
    
    Returns:
        Environment type ('lambda', 'local', 'container', 'testing', 'unknown')
    """
    if is_testing_environment():
        return 'testing'
    elif is_lambda_environment():
        return 'lambda'
    elif os.path.exists('/.dockerenv'):
        return 'container'
    elif is_local_development():
        return 'local'
    else:
        return 'unknown'
