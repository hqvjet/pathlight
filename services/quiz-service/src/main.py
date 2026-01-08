from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import json
from contextlib import asynccontextmanager
from mangum import Mangum

from src.config import config
from src.database import get_engine, Base 
from src.routes.quiz_routes import router as quiz_router

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

def _env_flag(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "y", "on"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Quiz Service starting up")
    skip_db = (
        bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
        or not config.DATABASE_URL
        or bool(os.getenv("PYTEST_CURRENT_TEST"))
        or _env_flag("QUIZ_SERVICE_SKIP_DB")
    )
    if skip_db:
        logger.info(
            "Skipping database setup | AWS_LAMBDA_FUNCTION_NAME=%s, DATABASE_URL_set=%s, PYTEST=%s, QUIZ_SERVICE_SKIP_DB=%s",
            bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME")), bool(config.DATABASE_URL), bool(os.getenv("PYTEST_CURRENT_TEST")), _env_flag("QUIZ_SERVICE_SKIP_DB"),
        )
    else:
        try:
            engine = get_engine()
            Base.metadata.create_all(bind=engine)
            logger.info("Database setup completed successfully for quiz service")
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            raise
    yield
    logger.info("Quiz Service shutting down")

app = FastAPI(
    title="Pathlight Quiz Service",
    description="Standalone Quiz Service for Pathlight Platform",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS if hasattr(config, 'ALLOWED_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=config.ALLOWED_METHODS if hasattr(config, 'ALLOWED_METHODS') else ["*"],
    allow_headers=config.ALLOWED_HEADERS if hasattr(config, 'ALLOWED_HEADERS') else ["*"],
)

app.include_router(quiz_router, prefix="/quiz")

mangum_handler = Mangum(app, lifespan="off")

def handler(event, context):
    logger.info("Lambda Event:")
    logger.info(json.dumps(event))

    if "path" in event:
        if "redoc" in event["path"]:
            event["path"] = "/redoc"
        elif "openapi.json" in event["path"]:
            event["path"] = "/openapi.json"

    try:
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
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        }

@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    return get_redoc_html(
        openapi_url="openapi.json",
        title="Quiz Service - API Docs",
        redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js",
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("QUIZ_SERVICE_PORT", str(config.SERVICE_PORT)))
    logger.info("Starting Pathlight Quiz Service...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)