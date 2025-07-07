import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt as jose_jwt

from .config import config
from .database import get_db
from .models import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        logger.info(f"🔍 get_current_user: Processing token: {token[:20]}...")

        try:
            payload = jose_jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError as e:
            logger.error(f"🔍 get_current_user: JWT Error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token expired or invalid: {str(e)}")

        logger.info(f"🔍 get_current_user: Token decoded successfully. Payload: {payload}")

        if payload.get("type") != "access":
            logger.warning(f"🔍 get_current_user: Invalid token type: {payload.get('type')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token type: {payload.get('type')}")

        user_id = payload.get("sub")
        if user_id is None:
            logger.warning(f"🔍 get_current_user: No user ID in token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no user id")

        logger.info(f"🔍 get_current_user: Looking for user with ID: {user_id}")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"🔍 get_current_user: User not found in database: {user_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        is_email_verified = getattr(user, 'is_email_verified', False)
        is_active = getattr(user, 'is_active', True)

        logger.info(f"🔍 get_current_user: User {user.email} - email_verified: {is_email_verified}, active: {is_active}")

        if not is_email_verified:
            logger.warning(f"🔍 get_current_user: Email not verified for user: {user.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")

        if not is_active:
            logger.warning(f"🔍 get_current_user: User account inactive: {user.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive")

        logger.info(f"🔍 get_current_user: Authentication successful for user: {user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 get_current_user: Unexpected error: {str(e)}")
        import traceback
        logger.error(f"🔍 get_current_user: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")

def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated admin user"""
    try:
        token = credentials.credentials
        logger.info(f"🔍 get_current_admin_user: Processing token: {token[:20]}...")

        try:
            payload = jose_jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError as e:
            logger.error(f"🔍 get_current_admin_user: JWT Error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token expired or invalid: {str(e)}")

        if payload.get("type") != "access":
            logger.warning(f"🔍 get_current_admin_user: Invalid token type: {payload.get('type')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token type: {payload.get('type')}")

        role = payload.get("role")
        if role != "admin":
            logger.warning(f"🔍 get_current_admin_user: Not an admin user")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        admin_id = payload.get("sub")
        if admin_id is None:
            logger.warning(f"🔍 get_current_admin_user: No admin ID in token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no admin id")

        # For admin, we can return a mock user object or handle differently
        # This depends on your admin model structure
        logger.info(f"🔍 get_current_admin_user: Admin authentication successful: {admin_id}")
        
        # Return a mock admin user or actual admin object
        class MockAdmin:
            def __init__(self, id):
                self.id = id
                self.email = "admin@pathlight.com"
                self.role = "admin"
        
        return MockAdmin(admin_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 get_current_admin_user: Unexpected error: {str(e)}")
        import traceback
        logger.error(f"🔍 get_current_admin_user: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")
