import bcrypt
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt as jose_jwt
from sqlalchemy.orm import Session
from typing import Optional

from ..config import config
from ..models import User, Admin, TokenBlacklist

def hash_password(password: str, *, rounds: int = 10) -> str:
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=60)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "type": "access",
        "iat": int(now.timestamp())
    })
    return jose_jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm="HS256")

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=7)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "type": "refresh", 
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp())
    })
    return jose_jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm="HS256")

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def create_user(db: Session, email: str, password: str, google_id: Optional[str] = None) -> User:
    verification_token = generate_token()
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=10)
    hashed_password = hash_password(password)
    if google_id == "":
        google_id = None
    
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
