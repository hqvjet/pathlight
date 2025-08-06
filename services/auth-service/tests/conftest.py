"""
Test configuration and fixtures for auth-service tests
"""
import pytest
import os
import sys
from unittest.mock import MagicMock

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

@pytest.fixture(autouse=True)
def setup_env():
    """Setup environment variables for testing"""
    os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
    os.environ.setdefault('JWT_SECRET_KEY', 'test_secret_key_for_testing')
    os.environ.setdefault('SMTP_USERNAME', 'test@example.com')
    os.environ.setdefault('SMTP_PASSWORD', 'test_password')
    os.environ.setdefault('FRONTEND_URL', 'http://localhost:3000')

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    from unittest.mock import MagicMock
    
    config = MagicMock()
    config.SMTP_USERNAME = "test@example.com"
    config.SMTP_PASSWORD = "test_password"
    config.FRONTEND_URL = "http://localhost:3000"
    config.JWT_SECRET_KEY = "test_secret_key"
    config.EMAIL_VERIFICATION_EXPIRE_MINUTES = 10
    config.ALLOWED_ORIGINS = ["http://localhost:3000"]
    config.ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE"]
    config.ALLOWED_HEADERS = ["*"]
    
    return config

@pytest.fixture
def mock_smtp_server():
    """Mock SMTP server for email testing"""
    mock_server = MagicMock()
    mock_server.starttls.return_value = None
    mock_server.login.return_value = None
    mock_server.sendmail.return_value = {}
    mock_server.quit.return_value = None
    return mock_server

@pytest.fixture
def mock_database():
    """Mock database session for testing"""
    mock_db = MagicMock()
    return mock_db
