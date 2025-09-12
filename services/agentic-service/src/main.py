import logging
from typing import Any, Dict
from dotenv import load_dotenv

from config import config
from handlers.sqs_handler import process_sqs_event
from contracts.sqs_contracts import SQSEvent, SQSBatchResponse

load_dotenv(override=True)

# Configure logging once for the worker
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Validate configuration at import for Lambda cold start fast-fail
_errors = config.validate_config()
if _errors:
    # Log only in local, raise in Lambda to surface misconfig
    logger.error(f"Configuration errors: {_errors}")
    if config.IS_LAMBDA:
        raise ValueError(f"Configuration errors: {_errors}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entrypoint for SQS-triggered processing.

    The handler delegates to process_sqs_event, which supports the following operations:
    - VECTORIZE_MATERIAL: build embeddings for documents listed in S3
    - GENERATE_COURSE: run the multi-agent pipeline to generate a course
    """
    # Validate/parse with schema; still return a plain dict for Lambda
    parsed = SQSEvent(**event)
    resp: SQSBatchResponse = process_sqs_event(parsed)
    return resp.model_dump()


# Optional: local debug runner to invoke with a sample SQS event
if __name__ == "__main__":
    logger.info("Running in local mode. Provide a sample SQS event to test.")
    # Minimal no-op
    print({"status": "ok", "message": "agentic-service ready for SQS events"})