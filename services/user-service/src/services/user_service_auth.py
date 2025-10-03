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

ADMIN_ACCESS_DENIED_MESSAGE = "Bạn không có quyền truy cập"

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

def _admin_access_denied_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=ADMIN_ACCESS_DENIED_MESSAGE,
    )


def _authorize_admin_internal(credentials: HTTPAuthorizationCredentials, db: Session) -> Admin:
    token = credentials.credentials
    try:
        payload = jose_jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        logger.error(f"Admin JWT Error: {str(e)}")
        raise _admin_access_denied_exception()

    if payload.get("type") != "access":
        logger.error(f"Admin token type invalid: {payload.get('type')}")
        raise _admin_access_denied_exception()

    if payload.get("role") != "admin":
        logger.error("Admin token missing admin role")
        raise _admin_access_denied_exception()

    admin_id = payload.get("sub")
    if not admin_id:
        logger.error("Admin token missing subject")
        raise _admin_access_denied_exception()

    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        logger.error(f"Admin not found in database: {admin_id}")
        raise _admin_access_denied_exception()

    return admin


def authorize_admin(
    credentials: HTTPAuthorizationCredentials,
    db: Session,
    raise_http_exception: bool = True,
) -> Admin | None:
    try:
        return _authorize_admin_internal(credentials, db)
    except HTTPException as exc:
        if raise_http_exception:
            raise
        logger.warning(f"Admin authorization failed: {exc.detail}")
        return None
    except Exception as e:
        logger.error(f"Unexpected admin authorization error: {str(e)}")
        if raise_http_exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )
        return None


def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Dependency that ensures admin-only access."""
    admin = authorize_admin(credentials, db, raise_http_exception=True)
    if admin is None:
        raise _admin_access_denied_exception()
    return admin
