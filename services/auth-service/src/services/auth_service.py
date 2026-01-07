import bcrypt
import secrets
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Optional
import logging
from google.oauth2 import id_token
from google.auth.transport import requests

from config import config
from models import User, UserProfile, Admin, TokenBlacklist

logger = logging.getLogger(__name__)

def hash_password(password: str, *, rounds: int = 10) -> str:
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def _create_token(data: dict, *, token_type: str, minutes: int) -> str:
    """Create a signed JWT with common claims for access/refresh tokens."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=minutes)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "type": token_type,
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
    })
    algorithm = getattr(config, "JWT_ALGORITHM", "HS256")
    if not isinstance(algorithm, str) or not algorithm:
        algorithm = "HS256"
    return jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=algorithm)


def create_access_token(data: dict) -> str:
    """Create a signed JWT access token (default 24h)."""
    expire_minutes_val = getattr(config, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
    try:
        expire_minutes = int(expire_minutes_val)
    except Exception:
        expire_minutes = 1440
    return _create_token(data, token_type="access", minutes=expire_minutes)


def create_refresh_token(data: dict) -> str:
    """Create a signed JWT refresh token (default 30 days)."""
    expire_minutes_val = getattr(config, "JWT_REFRESH_TOKEN_EXPIRE_MINUTES", 43200)  # 30 days
    try:
        expire_minutes = int(expire_minutes_val)
    except Exception:
        expire_minutes = 43200
    return _create_token(data, token_type="refresh", minutes=expire_minutes)

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def _create_profile(db: Session) -> UserProfile:
    profile = UserProfile(
        profile_id=str(uuid.uuid4()),
        subscription=0,
        streak=0,
        level=1,
        current_exp=0,
        require_exp=10,
    )
    db.add(profile)
    return profile


def create_user(db: Session, email: str, password: str, google_id: Optional[str] = None) -> User:
    verification_token = generate_token()
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=10)
    hashed_password = hash_password(password)
    if google_id == "":
        google_id = None

    try:
        profile = _create_profile(db)
        db.flush()

        user = User(
            email=email,
            password=hashed_password,
            google_id=google_id,
            email_verification_token=verification_token,
            email_verification_expires_at=expiration_time,
            is_email_verified=False,
            profile_id=profile.profile_id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_verification_token(db: Session, token: str) -> Optional[User]:
    return db.query(User).filter(User.email_verification_token == token).first()

def get_user_by_reset_token(db: Session, token: str) -> Optional[User]:
    return db.query(User).filter(User.password_reset_token == token).first()

def get_admin_by_username(db: Session, username: str) -> Optional[Admin]:
    return db.query(Admin).filter(Admin.username == username).first()

def verify_email_token(db: Session, user: User) -> bool:
    setattr(user, 'is_email_verified', True)
    setattr(user, 'email_verification_token', None)
    setattr(user, 'email_verification_expires_at', None)
    db.commit()
    return True

def blacklist_token(db: Session, jti: str) -> None:
    import logging
    logger = logging.getLogger(__name__)
    expire_hours = getattr(config, "TOKEN_BLACKLIST_EXPIRE_HOURS", 24)
    expire_time = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    try:
        blacklist_entry = TokenBlacklist(token=jti, expires_at=expire_time)
        db.add(blacklist_entry)
        db.commit()
        logger.info(f"Token {jti} blacklisted until {expire_time}")
    except Exception as e:
        logger.error(f"Failed to blacklist token {jti}: {str(e)}")

def is_token_blacklisted(db: Session, jti: str) -> bool:
    return db.query(TokenBlacklist).filter(TokenBlacklist.token == jti).first() is not None


def verify_google_token(token: str) -> Optional[dict]:
    """
    Verify Google ID token and return user information
    
    Args:
        token: Google ID token (JWT) received from frontend
        
    Returns:
        dict with user info (sub, email, given_name, family_name, picture) or None if invalid
    """
    try:
        if not config.GOOGLE_CLIENT_ID:
            logger.error("GOOGLE_CLIENT_ID not configured, cannot verify Google token")
            return None
            
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            config.GOOGLE_CLIENT_ID
        )
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            logger.error(f"Invalid token issuer: {idinfo['iss']}")
            return None
        
        logger.info(f"Successfully verified Google token for user: {idinfo.get('email')}")
        return {
            'sub': idinfo['sub'],  # Google user ID
            'email': idinfo['email'],
            'email_verified': idinfo.get('email_verified', False),
            'given_name': idinfo.get('given_name', ''),
            'family_name': idinfo.get('family_name', ''),
            'picture': idinfo.get('picture', ''),
        }
        
    except ValueError as e:
        logger.error(f"Google token verification failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying Google token: {str(e)}")
        return None

