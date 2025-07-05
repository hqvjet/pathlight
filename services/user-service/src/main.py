from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Import local modules
from .config import config
from .database import create_tables, engine
from .routes.user_routes import router as user_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Pathlight User Service",
    description="Standalone User Management Service for Pathlight Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for standalone service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers without prefix (direct access)
app.include_router(user_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize the service on startup"""
    try:
        logger.info("🚀 Starting Pathlight User Service...")
        
        # Test database connection
        with engine.connect() as connection:
            logger.info("✅ Database connection successful")
        
        # Create tables if they don't exist
        create_tables()
        logger.info("✅ Database tables created/verified")
        
        logger.info("🎉 User service started successfully!")
        logger.info(f"📝 API Documentation available at: http://localhost:{config.SERVICE_PORT}/docs")
        
    except Exception as e:
        logger.error(f"❌ Failed to start service: {str(e)}")
        raise

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - service information"""
    return {
        "service": "Pathlight User Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with engine.connect() as connection:
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy",
        "service": "user-service",
        "database": db_status,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    from .config import config
    
    logger.info("🚀 Starting Pathlight User Service directly...")
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0", 
        port=config.SERVICE_PORT, 
        reload=config.DEBUG,
        log_level="info" if not config.DEBUG else "debug"
    )
