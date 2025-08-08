import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt as jose_jwt

from config import config
from database import get_db
from models import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        try:
            payload = jose_jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError as e:
            logger.error(f"JWT Error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token expired or invalid: {str(e)}")
        if payload.get("type") != "access":
            logger.error(f"Invalid token type: {payload.get('type')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token type: {payload.get('type')}")
        user_id = payload.get("sub")
        if user_id is None:
            logger.error("No user ID in token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no user id")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found in database: {user_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        is_email_verified = getattr(user, 'is_email_verified', False)
        is_active = getattr(user, 'is_active', True)
        if not is_email_verified:
            logger.error(f"Email not verified for user: {user.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")
        if not is_active:
            logger.error(f"User account inactive: {user.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")

def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated admin user"""
    try:
        token = credentials.credentials
        try:
            payload = jose_jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError as e:
            logger.error(f"JWT Error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token expired or invalid: {str(e)}")
        if payload.get("type") != "access":
            logger.error(f"Invalid token type: {payload.get('type')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token type: {payload.get('type')}")
        role = payload.get("role")
        if role != "admin":
            logger.error("Not an admin user")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        admin_id = payload.get("sub")
        if admin_id is None:
            logger.error("No admin ID in token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no admin id")
        class MockAdmin:
            def __init__(self, id):
                self.id = id
                self.email = "admin@pathlight.com"
                self.role = "admin"
        return MockAdmin(admin_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")
