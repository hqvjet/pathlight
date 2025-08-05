import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from mangum import Mangum

load_dotenv(override=True)  # Override existing .env variables

# Import config from the clean config package
from config import config

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
    

from routers.file_routes import router as file_router

# Create FastAPI instance
app = FastAPI(
    title="Agentic Service - Restructured",
    description="🚀 Beautifully restructured service for file processing, vectorization, and AI-powered document analysis",
    version="2.0.0",
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
        "MAX_TOKENS_PER_CHUNK": config.MAX_TOKENS_PER_CHUNK,
        "MAX_FILE_SIZE_BYTES": config.MAX_FILE_SIZE_BYTES,
        "ALLOWED_FILE_EXTENSIONS": list(config.ALLOWED_FILE_EXTENSIONS),
        "OPENAI_API_KEY_SET": bool(config.OPENAI_API_KEY),
        "LOG_LEVEL": config.LOG_LEVEL,
        "OPENSEARCH_HOST": config.OPENSEARCH_HOST,
        "OPENSEARCH_PORT": config.OPENSEARCH_PORT,
        "OPENSEARCH_USER_SET": bool(config.OPENSEARCH_USER),
        "OPENSEARCH_PASSWORD_SET": bool(config.OPENSEARCH_PASSWORD),
        "OPENSEARCH_USE_SSL": config.OPENSEARCH_USE_SSL,
        "OPENSEARCH_VERIFY_CERTS": config.OPENSEARCH_VERIFY_CERTS,
        "S3_BUCKET_NAME": config.S3_BUCKET_NAME,
        "REGION": config.REGION
    }

@app.get("/debug/opensearch")
async def debug_opensearch():
    """Debug endpoint to test OpenSearch connection"""
    from controllers.file_controller import FileController
    
    try:
        controller = FileController()
        if not controller.opensearch_client:
            return {
                "status": "error",
                "message": "OpenSearch client not initialized",
                "config": {
                    "host": config.OPENSEARCH_HOST,
                    "port": config.OPENSEARCH_PORT,
                    "use_ssl": config.OPENSEARCH_USE_SSL,
                    "verify_certs": config.OPENSEARCH_VERIFY_CERTS
                }
            }
        
        # Test connection
        info = controller.opensearch_client.info()
        return {
            "status": "success",
            "message": "OpenSearch connection successful",
            "cluster_info": info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"OpenSearch connection failed: {str(e)}",
            "config": {
                "host": config.OPENSEARCH_HOST,
                "port": config.OPENSEARCH_PORT,
                "use_ssl": config.OPENSEARCH_USE_SSL,
                "verify_certs": config.OPENSEARCH_VERIFY_CERTS
            }
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
        log_level=config.LOG_LEVEL.lower(),
        timeout_keep_alive=60  # Keep-alive timeout for long-running requests
    )