from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from contextlib import asynccontextmanager
from mangum import Mangum
import json

from src.config import config
from src.database import create_tables, engine
from src.routes.course_routes import router as course_router

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def _env_flag(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "y", "on"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Course Service starting up")

    skip_db = (
        bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
        or not config.DATABASE_URL
        or bool(os.getenv("PYTEST_CURRENT_TEST"))
        or _env_flag("COURSE_SERVICE_SKIP_DB")
    )
    if skip_db:
        logger.info(
            "Skipping database setup | AWS_LAMBDA_FUNCTION_NAME=%s, DATABASE_URL_set=%s, PYTEST=%s, COURSE_SERVICE_SKIP_DB=%s",
            bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME")), bool(config.DATABASE_URL), bool(os.getenv("PYTEST_CURRENT_TEST")), _env_flag("COURSE_SERVICE_SKIP_DB"),
        )
    else:
        try:
            create_tables()
            logger.info("Database setup completed successfully")
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            raise

    yield

    logger.info("Course Service shutting down")


app = FastAPI(
    title="Pathlight Course Service",
    description="Standalone Course Service for Pathlight Platform",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(course_router, prefix="/course")

mangum_handler = Mangum(app, lifespan="off")

def handler(event, context):
    logger.info("Lambda Event:")
    logger.info(json.dumps(event))

    if "path" in event and "redoc" in event["path"]:
        logger.info(f"ReDoc path detected: {event['path']} -> /redoc")
        event["path"] = "/redoc"

    if "path" in event and "openapi.json" in event["path"]:
        logger.info(f"OpenAPI path detected: {event['path']} -> /openapi.json")
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("COURSE_SERVICE_PORT", config.SERVICE_PORT))
    logger.info("Starting Pathlight Course Service...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    return get_redoc_html(
        openapi_url="openapi.json", 
        title="Course Service - API Docs",
        js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"
    )
