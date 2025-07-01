from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging

# Import config
from .config import Config, Routes

# Setup logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PathLight API Gateway",
    description="Central API Gateway for PathLight Microservices - All client requests go through here",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=Config.ALLOWED_METHODS,
    allow_headers=Config.ALLOWED_HEADERS,
)

# HTTP client for forwarding requests to services
http_client = httpx.AsyncClient(timeout=Config.SERVICE_TIMEOUT)

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

async def forward_request(service: str, path: str, request: Request):
    """Forward request to the appropriate microservice"""
    if service not in Config.SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    service_url = Config.SERVICES[service]
    url = f"{service_url}{path}"

    headers = dict(request.headers)
    headers.pop("host", None) 
    
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
        return JSONResponse(
            content={"status": 503, "message": f"Service {service} unavailable"},
            status_code=503
        )
    except Exception as e:
        logger.error(f"Unexpected error forwarding to {url}: {str(e)}")
        return JSONResponse(
            content={"status": 500, "message": "Internal server error"},
            status_code=500
        ) 

@app.get("/")
async def root():
    return {
        "message": "PathLight API Gateway",
        "version": "1.0.0",
        "services": list(Config.SERVICES.keys()),
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Check health of all services"""
    health_status = {"gateway": "healthy", "services": {}}
    
    for service_name, service_url in Config.SERVICES.items():
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

@app.get("/api/v1/validate-reset-token/{token}")
async def validate_reset_token(token: str, request: Request):
    return await forward_request("auth", f"/api/v1/validate-reset-token/{token}", request)

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

@app.post("/api/v1/resend-verification")
async def resend_verification(request: Request):
    return await forward_request("auth", "/api/v1/resend-verification", request)

@app.put("/api/v1/user/notify-time")
async def set_notify_time(request: Request):
    return await forward_request("auth", "/api/v1/user/notify-time", request)

@app.get("/api/v1/user/profile")
async def get_user_profile(request: Request):
    return await forward_request("auth", "/api/v1/user/profile", request)

@app.get("/api/v1/admin/users")
async def get_all_users(request: Request):
    return await forward_request("auth", "/api/v1/admin/users", request)

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
    uvicorn.run(app, host=Config.GATEWAY_HOST, port=Config.GATEWAY_PORT)
