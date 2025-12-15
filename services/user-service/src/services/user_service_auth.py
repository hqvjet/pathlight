import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt as jose_jwt

from config import config
from database import get_db
from models import User, Admin

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
    """Resolve and return the current authenticated admin user"""
    def _deny_access(reason: str):
        logger.error(f"Admin access denied: {reason}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Bạn không có quyền truy cập")

    try:
        token = credentials.credentials
        payload = {}  # ensure payload is always bound for static analysis
        try:
            payload = jose_jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError as e:
            logger.error(f"JWT Error: {str(e)}")
            _deny_access("token invalid or expired")
        if payload.get("type") != "access":
            _deny_access(f"invalid token type: {payload.get('type')}")
        # Check role - must be admin
        role = payload.get("role")
        if role != "admin":
            _deny_access(f"role is not admin: {role}")
        admin_id = payload.get("sub")
        if not admin_id:
            _deny_access("missing admin id")
        # Return a dummy admin object with the ID from token
        # No need to verify against local database since auth-service already validated it
        admin = type('Admin', (), {'id': admin_id, 'username': 'admin'})()
        return admin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while resolving admin: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        _deny_access("internal error")
