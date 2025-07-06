import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from mangum import Mangum

load_dotenv('.')

from config import config
from routers import file_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate configuration
config_errors = config.validate_config()
if config_errors:
    logger.error(f"Configuration errors: {config_errors}")
    if config.IS_LAMBDA:
        raise ValueError(f"Configuration errors: {config_errors}")

# Create FastAPI instance
app = FastAPI(
    title="Agentic Service",
    description="Service for file processing, vectorization, and AI-powered document analysis",
    version="1.0.0",
    docs_url="/docs" if not config.IS_LAMBDA else None,  # Disable docs in Lambda
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=config.ALLOWED_METHODS,
    allow_headers=config.ALLOWED_HEADERS,
)

# Include routers
app.include_router(file_router)

# Health check endpoints
@app.get("/")
async def root():
    return {
        "message": "Agentic Service is running", 
        "version": "1.0.0",
        "environment": "lambda" if config.IS_LAMBDA else "local"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": "agentic-service",
        "environment": "lambda" if config.IS_LAMBDA else "local"
    }

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (without sensitive data)"""
    return {
        "IS_LAMBDA": config.IS_LAMBDA,
        "AWS_REGION": config.AWS_REGION,
        "AWS_S3_BUCKET_NAME": config.AWS_S3_BUCKET_NAME,
        "MAX_TOKENS_PER_CHUNK": config.MAX_TOKENS_PER_CHUNK,
        "MAX_FILE_SIZE_MB": config.MAX_FILE_SIZE_MB,
        "ALLOWED_FILE_EXTENSIONS": list(config.ALLOWED_FILE_EXTENSIONS),
        "OPENAI_API_KEY_SET": bool(config.OPENAI_API_KEY),
        "AWS_CREDENTIALS_SET": bool(config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY),
        "LOG_LEVEL": config.LOG_LEVEL,
    }

# AWS Lambda handler
handler = Mangum(app, lifespan="off")

# Local development server
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on port {config.SERVICE_PORT}")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=config.SERVICE_PORT, 
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )