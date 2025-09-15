
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from contextlib import asynccontextmanager
from mangum import Mangum
import json

from config import config
from database import create_tables, engine, SessionLocal
from routes.user_routes import router as user_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("User Service starting up")
    
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        logger.info("Running on AWS Lambda - skipping database setup")
    else:
        try:
            create_tables()
            logger.info("Database setup completed successfully")
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            raise
    
    yield
    
    # Shutdown
    logger.info("User Service shutting down")

"""
NOTE ABOUT DOCS BEHIND API GATEWAY STAGE
----------------------------------------
When deployed behind API Gateway with a stage (e.g. /api) and an additional
service base path (/user) provided via a greedy proxy, the default FastAPI
Swagger UI (docs_url="/docs") points to an absolute OpenAPI schema URL
"/openapi.json". The browser then requests https://<domain>/openapi.json
which bypasses the stage + service prefix and API Gateway returns 403.

Solution: disable the built-in docs and serve a custom Swagger UI whose
openapi_url is RELATIVE ("openapi.json" – no leading slash). This makes the
browser request the schema at the current path base, ending up correctly at
<domain>/api/user/openapi.json.
"""

app = FastAPI(
    title="Pathlight User Service",
    description="Standalone User Management Service for Pathlight Platform",
    version="1.0.0",
    docs_url=None,  # We'll provide a custom /docs endpoint with relative schema path
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You may want to use config.ALLOWED_ORIGINS if defined
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/user")

@app.get("/")
async def root():
    return {
        "service": "Pathlight User Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    try:
        with engine.connect():
            db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    return {
        "status": "healthy",
        "service": "user-service",
        "database": db_status,
        "version": "1.0.0"
    }

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration"""
    return {
        "SERVICE_NAME": config.SERVICE_NAME,
        "SERVICE_PORT": config.SERVICE_PORT,
        "DATABASE_URL": config.DATABASE_URL[:50] + "..." if config.DATABASE_URL else None,
        "JWT_SECRET_KEY": config.JWT_SECRET_KEY[:10] + "..." if config.JWT_SECRET_KEY else None,
        "FRONTEND_URL": config.FRONTEND_URL,
        "S3_USER_BUCKET_NAME": config.S3_USER_BUCKET_NAME,
    }

# AWS Lambda handler
mangum_handler = Mangum(app, lifespan="off")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_docs():
    """Custom Swagger UI with relative OpenAPI schema path.

    Using a relative path avoids losing the API Gateway stage (/api) and the
    service base path (/user) when the browser fetches the schema.
    """
    return get_swagger_ui_html(
        openapi_url="openapi.json",  # relative path (no leading slash!)
        title="Pathlight User Service - API Docs",
    )

def handler(event, context):
    """
    Custom Lambda handler for debugging and processing API Gateway events
    """
    # Log the complete event for debugging
    logger.info("Lambda Event:")
    logger.info(json.dumps(event))
    
    # Check if path contains "docs" and modify the path
    if "path" in event and "docs" in event["path"]:
        logger.info(f"Docs path detected: {event['path']} -> /docs")
        event["path"] = "/docs"
    
    # Check if path contains "redoc" and modify the path
    if "path" in event and "redoc" in event["path"]:
        logger.info(f"Redoc path detected: {event['path']} -> /redoc")
        event["path"] = "/redoc"
        
    if "path" in event and "openapi.json" in event["path"]:
        logger.info(f"OpenAPI path detected: {event['path']} -> /openapi.json")
        event["path"] = "/openapi.json"
    
    try:
        # Process the request through Mangum
        response = mangum_handler(event, context)
        logger.info(f"Response Status: {response.get('statusCode', 'Unknown')}")
        return response
    except Exception as e:
        logger.error(f"Error in Lambda handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "detail": str(e)}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("USER_SERVICE_PORT", "8004"))
    logger.info("Starting Pathlight User Service...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
