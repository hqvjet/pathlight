"""
Shared infrastructure clients

Initialize OpenSearch, OpenAI, and S3 clients once and reuse across modules.
"""

from dataclasses import dataclass
from typing import Optional

from config import config
from core.logging import setup_logger
from infrastructure.aws.s3_client import S3Client
from infrastructure.aws.opensearch_client import OpenSearchClient
from infrastructure.openai.client import OpenAIClient


logger = setup_logger(__name__)


@dataclass
class Clients:
    s3: S3Client
    opensearch: Optional[OpenSearchClient]
    openai: OpenAIClient


def _init_s3() -> S3Client:

    return S3Client(
        region=config.REGION,
        access_key_id=config.ACCESS_KEY_ID,
        secret_access_key=config.SECRET_ACCESS_KEY,
    )


def _init_opensearch() -> Optional[OpenSearchClient]:
    try:
        client = OpenSearchClient(
            host=config.OPENSEARCH_HOST,
            port=config.OPENSEARCH_PORT,
            username=config.OPENSEARCH_USER,
            password=config.OPENSEARCH_PASSWORD,
            use_ssl=config.OPENSEARCH_USE_SSL,
            verify_certs=config.OPENSEARCH_VERIFY_CERTS,
            timeout=config.OPENSEARCH_TIMEOUT,
            enabled=config.OPENSEARCH_ENABLED,
            skip_local=config.SKIP_OPENSEARCH_LOCAL,
            force_local=config.FORCE_OPENSEARCH_LOCAL,
        )
        return client
    except Exception as e:
        logger.warning(f"OpenSearch client initialization failed, continuing without it: {e}")
        return None


def _init_openai() -> OpenAIClient:
    return OpenAIClient(api_key=config.OPENAI_API_KEY, model=config.EMBEDDING_MODEL)


def init_clients() -> Clients:
    """Initialize and return shared clients."""
    logger.info("Initializing shared infrastructure clients (S3, OpenSearch, OpenAI)...")
    s3 = _init_s3()
    os_client = _init_opensearch()
    oa = _init_openai()
    logger.info("Shared clients initialized")
    return Clients(s3=s3, opensearch=os_client, openai=oa)


# Initialize once at module import
clients = init_clients()

__all__ = ["clients", "Clients", "init_clients"]
