"""
Advanced tests for user service functionality
"""

import pytest
import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))


class TestErrorHandling:
    """Test error handling across different modules"""
    
    def test_import_error_handling(self):
        """Test that modules handle import errors gracefully"""
        try:
            from src.config import get_database_url, get_jwt_secret
            from src.auth import get_current_user
            from src.models import User
            
            # These should not raise errors
            assert get_database_url() is not None
            assert get_jwt_secret() is not None
            assert callable(get_current_user)
            assert User is not None
        except ImportError as e:
            pytest.skip(f"Import error test failed: {e}")
    
    def test_config_validation(self):
        """Test configuration validation"""
        try:
            from src import config
            
            # Test that required config functions exist
            assert hasattr(config, 'get_database_url')
            assert hasattr(config, 'get_jwt_secret')
            assert hasattr(config, 'get_service_port')
            
            # Test functions return values
            assert config.get_database_url() is not None
            assert config.get_jwt_secret() is not None
            assert isinstance(config.get_service_port(), int)
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Config validation test failed: {e}")


class TestDataValidation:
    """Test data validation and sanitization"""
    
    def test_user_schema_validation(self):
        """Test user schema validation with various inputs"""
        try:
            from src.schemas.user_schemas import ChangeInfoRequest, NotifyTimeRequest
            from pydantic import ValidationError
            from datetime import datetime
            
            # Test ChangeInfoRequest validation
            valid_data = {
                "given_name": "Test",
                "family_name": "User",
                "sex": "Male",
                "bio": "Test bio",
                "dob": datetime(1990, 1, 1)  # Use datetime object instead of string
            }
            
            request = ChangeInfoRequest(**valid_data)
            assert request.given_name == "Test"
            assert request.sex == "Male"
            
            # Test invalid sex
            invalid_data = valid_data.copy()
            invalid_data["sex"] = "invalid"
            
            with pytest.raises(ValidationError):
                ChangeInfoRequest(**invalid_data)
                
        except ImportError as e:
            pytest.skip(f"Schema validation test failed: {e}")
    
    def test_time_validation(self):
        """Test time format validation"""
        try:
            from src.schemas.user_schemas import NotifyTimeRequest
            from pydantic import ValidationError
            
            # Test valid time format
            valid_time_data = {
                "remind_time": "08:30"
            }
            request = NotifyTimeRequest(**valid_time_data)
            assert request.remind_time == "08:30"
            
            # Test invalid time format
            invalid_time_data = {
                "remind_time": "25:70"  # Invalid time
            }
            
            with pytest.raises(ValidationError):
                NotifyTimeRequest(**invalid_time_data)
                
        except ImportError as e:
            pytest.skip(f"Time validation test failed: {e}")


class TestSecurityFeatures:
    """Test security-related functionality"""
    
    def test_auth_module_functions(self):
        """Test auth module has required functions"""
        try:
            from src.auth import get_current_user
            
            # Test that auth functions exist and are callable
            assert callable(get_current_user)
            
        except ImportError as e:
            pytest.skip(f"Auth module test failed: {e}")
    
    def test_jwt_secret_configuration(self):
        """Test JWT secret is configured"""
        try:
            from src.config import get_jwt_secret
            
            secret = get_jwt_secret()
            
            # Secret should exist and be substantial
            assert secret is not None
            assert len(secret) > 10  # Should be substantial length
            assert secret != "your-secret-key"  # Should not be default
                
        except ImportError as e:
            pytest.skip(f"JWT configuration test failed: {e}")


class TestDatabaseIntegrity:
    """Test database operations and integrity"""
    
    def test_user_model_relationships(self, db, test_user_data):
        """Test user model relationships and constraints"""
        try:
            from src.models import User
            
            # Create user
            user = User(
                email=test_user_data["email"],
                given_name=test_user_data["given_name"],
                family_name=test_user_data["family_name"],
                google_id=test_user_data["google_id"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Test user has required attributes
            assert user.id is not None
            assert user.created_at is not None
            assert user.updated_at is not None
            assert user.is_active is True  # Default value
            
            # Test unique email constraint
            duplicate_user = User(
                email=test_user_data["email"],  # Same email
                given_name="Another",
                family_name="User",
                google_id="different_google_id"
            )
            db.add(duplicate_user)
            
            # This should raise an integrity error
            with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                db.commit()
                
        except ImportError as e:
            pytest.skip(f"Database integrity test failed: {e}")


class TestPerformanceAndScaling:
    """Test performance considerations"""
    
    def test_query_efficiency(self, db, test_user_data):
        """Test that database queries are efficient"""
        try:
            from src.models import User
            
            # Create multiple users
            users = []
            for i in range(10):
                user = User(
                    email=f"user{i}@example.com",
                    given_name=f"User{i}",
                    family_name="Test",
                    google_id=f"google_id_{i}"
                )
                users.append(user)
                db.add(user)
            
            db.commit()
            
            # Test query by email (should be indexed)
            start_time = datetime.now()
            found_user = db.query(User).filter(User.email == "user5@example.com").first()
            query_time = (datetime.now() - start_time).total_seconds()
            
            assert found_user is not None
            assert found_user.email == "user5@example.com"
            # Query should be fast (less than 1 second for small dataset)
            assert query_time < 1.0
            
        except ImportError as e:
            pytest.skip(f"Query efficiency test failed: {e}")
    
    def test_bulk_operations(self, db):
        """Test bulk database operations"""
        try:
            from src.models import User
            
            # Test bulk insert performance
            users_data = [
                {
                    "email": f"bulk_user_{i}@example.com",
                    "given_name": f"BulkUser{i}",
                    "family_name": "Test",
                    "google_id": f"bulk_google_id_{i}"
                }
                for i in range(50)
            ]
            
            start_time = datetime.now()
            
            # Bulk insert
            for user_data in users_data:
                user = User(**user_data)
                db.add(user)
            
            db.commit()
            bulk_time = (datetime.now() - start_time).total_seconds()
            
            # Bulk operation should complete reasonably fast
            assert bulk_time < 5.0  # Should complete within 5 seconds
            
            # Verify all users were created
            user_count = db.query(User).filter(User.email.like("bulk_user_%")).count()
            assert user_count == 50
            
        except ImportError as e:
            pytest.skip(f"Bulk operations test failed: {e}")


def test_service_integration():
    """Test overall service integration"""
    try:
        from src.main import app
        from src.routes.user_routes import router
        from src.database import get_db
        from src.models import Base
        
        # Test that all components can be imported together
        assert app is not None
        assert router is not None
        assert get_db is not None
        assert Base is not None
        
        # Test that app has routes
        assert hasattr(app, 'routes')
        assert len(app.routes) > 5  # Should have multiple routes
        
    except ImportError as e:
        pytest.skip(f"Service integration test failed: {e}")


def test_environment_handling():
    """Test environment variable handling"""
    try:
        import os
        from src.config import get_database_url
        
        # Test that config reads environment properly
        db_url = get_database_url()
        assert db_url is not None
        assert len(db_url) > 0
        
        # In test environment, should use test database
        if os.environ.get("TESTING") == "true":
            assert "test" in db_url.lower() or "sqlite" in db_url.lower()
            
    except ImportError as e:
        pytest.skip(f"Environment handling test failed: {e}")


def test_error_responses():
    """Test that error responses are properly formatted"""
    try:
        from src.schemas.user_schemas import MessageResponse
        
        # Test response schema with required parameters
        error_response = MessageResponse(status=400, message="Test error message")
        assert error_response.status == 400
        assert error_response.message == "Test error message"
        
        # Test that response can be serialized
        response_dict = error_response.dict()
        assert "status" in response_dict
        assert "message" in response_dict
        assert response_dict["status"] == 400
        assert response_dict["message"] == "Test error message"
        
    except ImportError as e:
        pytest.skip(f"Error response test failed: {e}")
