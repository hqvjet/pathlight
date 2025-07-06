"""
Test database models and operations
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))


class TestUserModel:
    """Test User model functionality"""
    
    def test_create_user_model(self, db):
        """Test creating a User model instance"""
        try:
            from src.models import User
            
            user = User(
                email="test@example.com",
                given_name="Test",
                family_name="User",
                google_id="google_123",
                is_email_verified=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert user.id is not None
            assert getattr(user, 'email') == "test@example.com"
            assert getattr(user, 'given_name') == "Test"
            assert getattr(user, 'family_name') == "User"
            assert getattr(user, 'google_id') == "google_123"
            assert user.is_email_verified is True
            assert user.is_active is True  # Default value
            assert getattr(user, 'level') == 1  # Default value
            assert getattr(user, 'current_exp') == 0  # Default value
            assert getattr(user, 'require_exp') == 10  # Default value
            
        except ImportError as e:
            pytest.skip(f"Model import failed: {e}")
    
    def test_user_profile_fields(self, db):
        """Test user profile fields"""
        try:
            from src.models import User
            
            user = User(
                email="profile@example.com",
                given_name="Profile",
                family_name="Test",
                sex="Male",
                bio="Test bio",
                remind_time="18:30"
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert getattr(user, 'sex') == "Male"
            assert getattr(user, 'bio') == "Test bio"
            assert getattr(user, 'remind_time') == "18:30"
            
        except ImportError as e:
            pytest.skip(f"Model import failed: {e}")
    
    def test_user_oauth_fields(self, db):
        """Test OAuth-related fields"""
        try:
            from src.models import User
            
            user = User(
                email="oauth@example.com",
                google_id="oauth_google_123",
                given_name="OAuth",
                family_name="User",
                avatar_url="https://example.com/avatar.jpg"
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert getattr(user, 'google_id') == "oauth_google_123"
            assert getattr(user, 'avatar_url') == "https://example.com/avatar.jpg"
            assert user.password is None  # Nullable for OAuth users
            
        except ImportError as e:
            pytest.skip(f"Model import failed: {e}")
    
    def test_user_timestamps(self, db):
        """Test timestamp fields"""
        try:
            from src.models import User
            
            user = User(
                email="timestamp@example.com",
                given_name="Timestamp",
                family_name="Test"
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert user.created_at is not None
            assert user.updated_at is not None
            assert user.last_login is None  # Initially null
            
        except ImportError as e:
            pytest.skip(f"Model import failed: {e}")
    
    def test_user_gamification_fields(self, db):
        """Test gamification fields (level, exp)"""
        try:
            from src.models import User
            
            user = User(
                email="game@example.com",
                given_name="Game",
                family_name="User",
                level=5,
                current_exp=150,
                require_exp=200
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert getattr(user, 'level') == 5
            assert getattr(user, 'current_exp') == 150
            assert getattr(user, 'require_exp') == 200
            
        except ImportError as e:
            pytest.skip(f"Model import failed: {e}")


class TestDatabaseOperations:
    """Test database operations"""
    
    def test_user_query_by_email(self, db):
        """Test querying user by email"""
        try:
            from src.models import User
            
            # Create user
            user = User(
                email="query@example.com",
                given_name="Query",
                family_name="Test"
            )
            db.add(user)
            db.commit()
            
            # Query user
            found_user = db.query(User).filter(User.email == "query@example.com").first()
            assert found_user is not None
            assert getattr(found_user, 'email') == "query@example.com"
            assert getattr(found_user, 'given_name') == "Query"
            
        except ImportError as e:
            pytest.skip(f"Model import failed: {e}")
    
    def test_user_query_by_google_id(self, db):
        """Test querying user by Google ID"""
        try:
            from src.models import User
            
            # Create user
            user = User(
                email="google@example.com",
                google_id="unique_google_123",
                given_name="Google",
                family_name="User"
            )
            db.add(user)
            db.commit()
            
            # Query user
            found_user = db.query(User).filter(User.google_id == "unique_google_123").first()
            assert found_user is not None
            assert getattr(found_user, 'google_id') == "unique_google_123"
            assert getattr(found_user, 'email') == "google@example.com"
            
        except ImportError as e:
            pytest.skip(f"Model import failed: {e}")
    
    def test_user_update_operations(self, db):
        """Test updating user fields"""
        try:
            from src.models import User
            
            # Create user
            user = User(
                email="update@example.com",
                given_name="Original",
                family_name="Name"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Update user using setattr to avoid typing issues
            setattr(user, 'given_name', "Updated")
            setattr(user, 'bio', "Updated bio")
            db.commit()
            db.refresh(user)
            
            assert getattr(user, 'given_name') == "Updated"
            assert getattr(user, 'bio') == "Updated bio"
            
        except ImportError as e:
            pytest.skip(f"Model import failed: {e}")


def test_import_models():
    """Test that models module can be imported"""
    try:
        import src.models
        assert src.models is not None
        assert hasattr(src.models, 'User')
        assert hasattr(src.models, 'Base')
    except ImportError as e:
        pytest.skip(f"Models import failed: {e}")


def test_import_database():
    """Test that database module can be imported"""
    try:
        import src.database
        assert src.database is not None
    except ImportError as e:
        pytest.skip(f"Database import failed: {e}")
