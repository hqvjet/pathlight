

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from .config import config
from .database import get_engine, Base
from src.routes.quiz_routes import router as quiz_router

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(title="Quiz Service", version="1.0.0")

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", str(config.SERVICE_PORT)))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
