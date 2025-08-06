"""
Business Logic Tests

Tests for authentication business logic including user creation,
password hashing, JWT tokens, email verification, and admin functions.
"""
import pytest
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestAuthService:
    """Test suite for authentication service business logic"""

    def test_hash_password(self):
        """Test password hashing functionality"""
        from services.auth_service import hash_password
        
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Verify hash is created
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        
        # Verify hash is different each time
        hashed2 = hash_password(password)
        assert hashed != hashed2

    def test_hash_password_with_custom_rounds(self):
        """Test password hashing with custom rounds"""
        from services.auth_service import hash_password
        
        password = "test_password"
        hashed = hash_password(password, rounds=8)
        
        assert hashed is not None
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        from services.auth_service import hash_password, verify_password
        
        password = "correct_password"
        hashed = hash_password(password)
        
        # Should return True for correct password
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        from services.auth_service import hash_password, verify_password
        
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        # Should return False for incorrect password
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_strings(self):
        """Test password verification with empty strings"""
        from services.auth_service import hash_password, verify_password
        
        # Hash empty password
        hashed = hash_password("")
        
        # Should verify empty password correctly
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False

    @patch('services.auth_service.config')
    def test_create_access_token(self, mock_config):
        """Test JWT access token creation"""
        mock_config.JWT_SECRET_KEY = "test_secret_key"
        
        from services.auth_service import create_access_token
        
        data = {"user_id": 123, "email": "test@example.com"}
        token = create_access_token(data)
        
        # Verify token is created
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token content
        decoded = jwt.decode(token, "test_secret_key", algorithms=["HS256"])
        assert decoded["user_id"] == 123
        assert decoded["email"] == "test@example.com"
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "iat" in decoded

    @patch('services.auth_service.config')
    def test_create_access_token_expiration(self, mock_config):
        """Test JWT token expiration is set correctly"""
        mock_config.JWT_SECRET_KEY = "test_secret_key"
        
        from services.auth_service import create_access_token
        
        before_time = datetime.now(timezone.utc)
        token = create_access_token({"user_id": 1})
        after_time = datetime.now(timezone.utc)
        
        decoded = jwt.decode(token, "test_secret_key", algorithms=["HS256"])
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        
        # Token should expire in approximately 60 minutes
        expected_min = before_time + timedelta(minutes=59)
        expected_max = after_time + timedelta(minutes=61)
        
        assert expected_min <= exp_time <= expected_max

    def test_generate_token(self):
        """Test random token generation"""
        from services.auth_service import generate_token
        
        token1 = generate_token()
        token2 = generate_token()
        
        # Verify tokens are created and unique
        assert token1 is not None
        assert token2 is not None
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        assert token1 != token2
        assert len(token1) > 30  # URL-safe base64 tokens are fairly long

    @patch('models.User')
    def test_create_user_basic(self, mock_user_class):
        """Test basic user creation"""
        # Setup mock database session and user class
        mock_db = MagicMock()
        mock_user_instance = MagicMock()
        mock_user_instance.email = "test@example.com"
        mock_user_instance.password = "hashed_password"
        mock_user_instance.google_id = None
        mock_user_instance.email_verification_token = "token123"
        mock_user_instance.email_verification_expires_at = MagicMock()
        mock_user_instance.is_email_verified = False
        
        mock_user_class.return_value = mock_user_instance
        
        from services.auth_service import create_user
        
        # Execute
        user = create_user(
            db=mock_db,
            email="test@example.com",
            password="password123"
        )
        
        # Verify user object
        assert user.email == "test@example.com"
        assert user.google_id is None
        assert user.email_verification_token is not None
        assert user.email_verification_expires_at is not None
        assert user.is_email_verified is False
        
        # Verify database operations
        mock_db.add.assert_called_once_with(user)
        mock_db.commit.assert_called_once()

    @patch('models.User')
    def test_create_user_with_google_id(self, mock_user_class):
        """Test user creation with Google ID"""
        mock_db = MagicMock()
        mock_user_instance = MagicMock()
        mock_user_instance.google_id = "google_123"
        mock_user_class.return_value = mock_user_instance
        
        from services.auth_service import create_user
        
        user = create_user(
            db=mock_db,
            email="test@example.com",
            password="password123",
            google_id="google_123"
        )
        
        assert user.google_id == "google_123"

    @patch('models.User')
    def test_create_user_empty_google_id(self, mock_user_class):
        """Test user creation with empty Google ID converts to None"""
        mock_db = MagicMock()
        mock_user_instance = MagicMock()
        mock_user_instance.google_id = None
        mock_user_class.return_value = mock_user_instance
        
        from services.auth_service import create_user
        
        user = create_user(
            db=mock_db,
            email="test@example.com",
            password="password123",
            google_id=""
        )
        
        assert user.google_id is None

    def test_get_user_by_email(self):
        """Test retrieving user by email"""
        from services.auth_service import get_user_by_email
        
        # Setup mock database and query
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = get_user_by_email(mock_db, "test@example.com")
        
        assert result == mock_user
        # Verify query was constructed correctly
        mock_db.query.assert_called_once()

    def test_get_user_by_verification_token(self):
        """Test retrieving user by verification token"""
        from services.auth_service import get_user_by_verification_token
        
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = get_user_by_verification_token(mock_db, "token123")
        
        assert result == mock_user

    def test_get_user_by_reset_token(self):
        """Test retrieving user by password reset token"""
        from services.auth_service import get_user_by_reset_token
        
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = get_user_by_reset_token(mock_db, "reset_token123")
        
        assert result == mock_user

    def test_get_admin_by_username(self):
        """Test retrieving admin by username"""
        from services.auth_service import get_admin_by_username
        
        mock_db = MagicMock()
        mock_admin = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_admin
        
        result = get_admin_by_username(mock_db, "admin")
        
        assert result == mock_admin

    def test_verify_email_token(self):
        """Test email verification process"""
        from services.auth_service import verify_email_token
        
        mock_db = MagicMock()
        mock_user = MagicMock()
        
        result = verify_email_token(mock_db, mock_user)
        
        assert result is True
        mock_db.commit.assert_called_once()

    @patch('services.auth_service.config')
    def test_blacklist_token(self, mock_config):
        """Test token blacklisting functionality"""
        mock_config.TOKEN_BLACKLIST_EXPIRE_HOURS = 24
        
        from services.auth_service import blacklist_token
        
        mock_db = MagicMock()
        
        # Execute
        blacklist_token(mock_db, "token_jti_123")
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_is_token_blacklisted_true(self):
        """Test checking if token is blacklisted - blacklisted case"""
        from services.auth_service import is_token_blacklisted
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        
        result = is_token_blacklisted(mock_db, "blacklisted_token")
        
        assert result is True

    def test_is_token_blacklisted_false(self):
        """Test checking if token is blacklisted - not blacklisted case"""
        from services.auth_service import is_token_blacklisted
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = is_token_blacklisted(mock_db, "clean_token")
        
        assert result is False


class TestTokenSecurity:
    """Test suite for token security features"""

    @patch('services.auth_service.config')
    def test_jwt_token_structure(self, mock_config):
        """Test JWT token has proper structure"""
        mock_config.JWT_SECRET_KEY = "secret_key_for_testing"
        
        from services.auth_service import create_access_token
        
        token = create_access_token({"user_id": 1, "role": "user"})
        
        # JWT tokens have 3 parts separated by dots
        parts = token.split('.')
        assert len(parts) == 3
        
        # Each part should be base64 encoded
        for part in parts:
            assert len(part) > 0

    @patch('services.auth_service.config')
    def test_jwt_token_cannot_be_modified(self, mock_config):
        """Test JWT token integrity - modification should fail verification"""
        mock_config.JWT_SECRET_KEY = "secret_key_for_testing"
        
        from services.auth_service import create_access_token
        
        token = create_access_token({"user_id": 1})
        
        # Modify the token
        modified_token = token[:-5] + "XXXXX"
        
        # Should raise exception when decoding modified token
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(modified_token, "secret_key_for_testing", algorithms=["HS256"])

    def test_password_hash_security(self):
        """Test password hashing security properties"""
        from services.auth_service import hash_password
        
        password = "secure_password_123"
        
        # Hash multiple times - should be different each time (salt)
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        hash3 = hash_password(password)
        
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3
        
        # All should be bcrypt hashes (start with $2b$)
        assert hash1.startswith('$2b$')
        assert hash2.startswith('$2b$')
        assert hash3.startswith('$2b$')
