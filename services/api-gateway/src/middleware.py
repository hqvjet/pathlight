from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class AuthMiddleware:
    def __init__(self):
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token with auth service"""
        try:
            response = await self.http_client.post(
                f"{self.auth_service_url}/api/auth/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = None) -> Optional[dict]:
        """Get current user from token"""
        if not credentials:
            return None
            
        user_data = await self.verify_token(credentials.credentials)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_data

# Rate limiting (simple in-memory implementation)
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for this IP"""
        now = time.time()
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True

# Global instances
auth_middleware = AuthMiddleware()
rate_limiter = RateLimiter()

# Protected endpoints that require authentication
PROTECTED_ENDPOINTS = {
    "/api/user/",
    "/api/course/",
    "/api/lesson/", 
    "/api/quiz/",
    "/api/test/"
}

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/api/auth/login",
    "/api/auth/register", 
    "/api/auth/refresh",
    "/health",
    "/"
}
