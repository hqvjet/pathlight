import os
import logging
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from src.config import config

logger = logging.getLogger(__name__)


def _ddb_table_name() -> str:
    return os.getenv("DDB_TABLE_NAME")


def _ddb_table():
    """Return a DynamoDB Table resource using configured credentials/region."""
    kwargs: Dict[str, Any] = {
        "region_name": getattr(config, "REGION", None) or os.getenv("REGION") or "ap-northeast-1",
    }
    if getattr(config, "ACCESS_KEY_ID", None) and getattr(config, "SECRET_ACCESS_KEY", None):
        kwargs["aws_access_key_id"] = config.ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = config.SECRET_ACCESS_KEY

    try:
        resource = boto3.resource("dynamodb", **kwargs)
        return resource.Table(_ddb_table_name())
    except Exception as e:
        logger.error("Failed to initialize DynamoDB table: %s", e)
        return None


def fetch_generation_status(course_id: str) -> Optional[Dict[str, Any]]:
    """Fetch and normalize generation status for a course from DynamoDB.

    Returns None when not found or on error.
    """
    table = _ddb_table()
    if table is None:
        return None
    try:
        resp = table.get_item(Key={"course_id": course_id})
        item = resp.get("Item")
        if not item:
            return None
        plan = bool(item.get("title_ready", False))
        lessons = bool(item.get("lessons_ready", False))
        final = bool(item.get("final_ready", False))
        vectorized = bool(item.get("vectorized", False))
        overall = plan and lessons and final
        return {
            "status": overall,
            "vectorized": vectorized,
            "generated_plan": plan,
            "generated_lessons": lessons,
            "generated_final_test": final,
            # Optional extras to help the UI if needed
            "progress": item.get("progress"),
            "updated_at": item.get("updated_at"),
        }
    except (ClientError, BotoCoreError) as e:
        logger.error("DynamoDB get_item error: %s", e)
        return None
