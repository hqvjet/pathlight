import logging
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer()

def require_bearer(credentials: HTTPAuthorizationCredentials = Depends(security)) -> HTTPAuthorizationCredentials:
    """Require a Bearer token and return the credential. Validation happens in controller."""
    return credentials
