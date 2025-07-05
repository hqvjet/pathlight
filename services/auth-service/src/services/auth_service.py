import bcrypt
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt as jose_jwt
from sqlalchemy.orm import Session
from typing import Optional

from ..config import config
from ..models import User, Admin, TokenBlacklist

# JWT Configuration
JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
JWT_REFRESH_TOKEN_EXPIRE_DAYS = config.JWT_REFRESH_TOKEN_EXPIRE_DAYS
EMAIL_VERIFICATION_EXPIRE_MINUTES = config.EMAIL_VERIFICATION_EXPIRE_MINUTES

def hash_password(password: str, *, rounds: int = 10) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "type": "access",
        "iat": int(now.timestamp())
    })
    return jose_jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "type": "refresh", 
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp())
    })
    return jose_jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def create_user(db: Session, email: str, password: str, google_id: Optional[str] = None) -> User:
    """Create a new user"""
    verification_token = generate_token()
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=EMAIL_VERIFICATION_EXPIRE_MINUTES)
    hashed_password = hash_password(password)
    
    user = User(
        email=email,
        password=hashed_password,
        google_id=google_id,
        email_verification_token=verification_token,
        email_verification_expires_at=expiration_time,
        is_email_verified=False
    )
    
    db.add(user)
    db.commit()
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_verification_token(db: Session, token: str) -> Optional[User]:
    """Get user by verification token"""
    return db.query(User).filter(User.email_verification_token == token).first()

def get_user_by_reset_token(db: Session, token: str) -> Optional[User]:
    """Get user by password reset token"""
    return db.query(User).filter(User.password_reset_token == token).first()

def get_admin_by_username(db: Session, username: str) -> Optional[Admin]:
    """Get admin by username"""
    return db.query(Admin).filter(Admin.username == username).first()

def verify_email_token(db: Session, user: User) -> bool:
    """Verify user's email and clear verification token"""
    setattr(user, 'is_email_verified', True)
    setattr(user, 'email_verification_token', None)
    setattr(user, 'email_verification_expires_at', None)
    db.commit()
    return True

def blacklist_token(db: Session, jti: str) -> None:
    """Add token to blacklist"""
    blacklist_token = TokenBlacklist(token_jti=jti)
    db.add(blacklist_token)
    db.commit()

def is_token_blacklisted(db: Session, jti: str) -> bool:
    """Check if token is blacklisted"""
    return db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first() is not None
