"""
Test configuration and fixtures for user service tests
"""

import pytest
import os
from unittest.mock import Mock

# Mock environment variables for testing
@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    os.environ.update({
        "DATABASE_URL": "sqlite:///./test.db",
        "JWT_SECRET_KEY": "test_secret_key_for_jwt_testing_12345",
        "USER_SERVICE_PORT": "8004",
        "ACCESS_KEY_ID": "test_access_key",
        "SECRET_ACCESS_KEY": "test_secret_key",
        "S3_USER_BUCKET_NAME": "test-bucket",
        "FRONTEND_URL": "http://localhost:3000"
    })

@pytest.fixture
def mock_user():
    """Mock user object for testing"""
    user = Mock()
    user.id = "test-user-id-123"
    user.email = "test@example.com"
    user.family_name = "Test"
    user.given_name = "User"
    user.level = 1
    user.current_exp = 0
    user.require_exp = 100
    user.is_active = True
    user.is_email_verified = True
    user.sex = "Male"
    user.bio = "Test bio"
    user.remind_time = "18:30"
    user.dob = None
    user.created_at = "2024-01-01T00:00:00Z"
    return user

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'id': 'user-123',
        'name': 'Test User',
        'exp': 500,
        'level': 3,
        'completed_courses': 2,
        'completed_quizzes': 5,
        'average_score': 0.85,
        'daily_streak': 7
    }
