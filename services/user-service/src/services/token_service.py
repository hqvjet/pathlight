import logging
from datetime import datetime, timedelta
from jose import jwt
from config import config

logger = logging.getLogger(__name__)

__all__ = ["create_access_token"]


def create_access_token(user_id: str, email: str | None = None, expires_minutes: int = 15) -> str:
    """Generate short-lived access token for service-to-service communication."""
    try:
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        payload = {"sub": user_id, "exp": int(expire.timestamp()), "type": "access"}
        if email:
            payload["email"] = email
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    except Exception as e:  # pragma: no cover
        logger.error(f"Error creating access token: {e}")
        return ""
