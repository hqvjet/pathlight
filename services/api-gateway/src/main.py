from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PathLight API Gateway",
    description="Central API Gateway for PathLight Microservices",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
}

# HTTP client
http_client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

async def forward_request(service: str, path: str, request: Request):
    """Forward request to the appropriate microservice"""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    service_url = SERVICES[service]
    url = f"{service_url}{path}"
    
    # Forward headers
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
    
    try:
        # Get request body for POST/PUT requests
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Forward request
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params
        )
        
        # Return response
        return JSONResponse(
            content=response.json() if response.content else {},
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.RequestError as e:
        logger.error(f"Request to {url} failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service {service} unavailable")
    except Exception as e:
        logger.error(f"Unexpected error forwarding to {url}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    return {
        "message": "PathLight API Gateway",
        "version": "1.0.0",
        "services": list(SERVICES.keys()),
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Check health of all services"""
    health_status = {"gateway": "healthy", "services": {}}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = await http_client.get(f"{service_url}/health", timeout=5.0)
            health_status["services"][service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": service_url
            }
        except Exception as e:
            health_status["services"][service_name] = {
                "status": "unreachable",
                "error": str(e),
                "url": service_url
            }
    
    return health_status

# Auth service routes
@app.post("/api/v1/signup")
async def signup(request: Request):
    return await forward_request("auth", "/api/v1/signup", request)

@app.get("/api/v1/verify-email")
async def verify_email(request: Request):
    return await forward_request("auth", "/api/v1/verify-email", request)

@app.post("/api/v1/signin")
async def signin(request: Request):
    return await forward_request("auth", "/api/v1/signin", request)

@app.get("/api/v1/signout")
async def signout(request: Request):
    return await forward_request("auth", "/api/v1/signout", request)

@app.post("/api/v1/forget-password")
async def forget_password(request: Request):
    return await forward_request("auth", "/api/v1/forget-password", request)

@app.post("/api/v1/reset-password/{token}")
async def reset_password(token: str, request: Request):
    return await forward_request("auth", f"/api/v1/reset-password/{token}", request)

@app.post("/api/v1/oauth-signin")
async def oauth_signin(request: Request):
    return await forward_request("auth", "/api/v1/oauth-signin", request)

@app.post("/api/v1/user/change-password")
async def change_password(request: Request):
    return await forward_request("auth", "/api/v1/user/change-password", request)

@app.post("/api/v1/admin/signin")
async def admin_signin(request: Request):
    return await forward_request("auth", "/api/v1/admin/signin", request)

# Catch-all route for other services
@app.api_route("/{service:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(service: str, request: Request):
    """Proxy requests to appropriate microservices"""
    # Extract service name from path
    path_parts = service.split("/", 1)
    if len(path_parts) < 2:
        raise HTTPException(status_code=404, detail="Invalid route")
    
    service_name = path_parts[0]
    remaining_path = "/" + path_parts[1] if len(path_parts) > 1 else "/"
    
    return await forward_request(service_name, remaining_path, request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
