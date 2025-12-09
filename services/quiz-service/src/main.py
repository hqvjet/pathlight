
from mangum import Mangum
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import json

from .config import config
from .database import get_engine, Base
from src.routes.quiz_routes import router as quiz_router

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(title="Quiz Service", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=config.ALLOWED_METHODS,
    allow_headers=config.ALLOWED_HEADERS,
)


@app.on_event("startup")
async def startup_event():
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured for quiz service")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "Quiz Service is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "quiz-service"}

@app.get("/debug/config")
async def debug_config():
    return {
        "DATABASE_URL": config.DATABASE_URL[:50] + "..." if config.DATABASE_URL else None,
        "JWT_SECRET_KEY": config.JWT_SECRET_KEY[:10] + "..." if config.JWT_SECRET_KEY else None,
        "ALLOWED_ORIGINS": config.ALLOWED_ORIGINS,
        "SERVICE_PORT": config.SERVICE_PORT,
    }

mangum_handler = Mangum(app, lifespan="off")

def handler(event, context):
    """
    Custom Lambda handler for debugging and processing API Gateway events
    """
    # Log the complete event for debugging
    logger.info("Lambda Event:")
    logger.info(json.dumps(event))
    
    # Check if path contains "docs" and modify the path
    # Only expose ReDoc (no Swagger) - normalize any redoc path variant
    if "path" in event and "redoc" in event["path"]:
        logger.info(f"ReDoc path detected: {event['path']} -> /redoc")
        event["path"] = "/redoc"

    # Normalize schema path (stage + service prefixes get stripped otherwise)
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
    port = int(os.getenv("SERVICE_PORT", str(config.SERVICE_PORT)))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    return get_redoc_html(
        openapi_url="openapi.json", 
        title="Quiz Service - API Docs",
        redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"
    )