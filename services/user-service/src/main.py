
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .config import config
from .database import create_tables, engine
from .routes.user_routes import router as user_router

logging.basicConfig(
    level=getattr(logging, getattr(config, "LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("user-service")

app = FastAPI(
    title="Pathlight User Service",
    description="Standalone User Management Service for Pathlight Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)

@app.on_event("startup")
async def startup_event():
    try:
        create_tables()
        logger.info("User service started.")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Pathlight User Service...")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=config.SERVICE_PORT,
        reload=getattr(config, "DEBUG", False),
        log_level="info" if not getattr(config, "DEBUG", False) else "debug"
    )
