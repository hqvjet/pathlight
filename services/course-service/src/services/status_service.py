import os
import logging
from typing import Optional, Dict, Any, List

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from src.config import config

logger = logging.getLogger(__name__)


def _ddb_table_name() -> str:
    # Default to the same table name used by agentic-service if not provided
    return os.getenv("DDB_TABLE_NAME", "pathlight-agentic-status")


def _ddb_table():
    """Return a DynamoDB Table resource using configured credentials/region."""
    kwargs: Dict[str, Any] = {
        "region_name": getattr(config, "REGION", None) or os.getenv("REGION") or "ap-northeast-1",
    }
    if getattr(config, "ACCESS_KEY_ID", None) and getattr(config, "SECRET_ACCESS_KEY", None):
        kwargs["aws_access_key_id"] = config.ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = config.SECRET_ACCESS_KEY
    endpoint = os.getenv("DDB_ENDPOINT_URL")
    if endpoint:
        kwargs["endpoint_url"] = endpoint

    table_name = _ddb_table_name()
    if not table_name:
        logger.error("DDB_TABLE_NAME not configured and no default available")
        return None

    try:
        resource: Any = boto3.resource("dynamodb", **kwargs)
        table = resource.Table(table_name)
        # Try a light call to ensure table exists/accessible
        try:
            table.load()
        except Exception:
            # We'll let scan/get handle specific errors later
            pass
        return table
    except Exception as e:
        logger.error("Failed to initialize DynamoDB table '%s': %s", table_name, e)
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


def fetch_user_generations(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Return all generation rows for the given user_id from DynamoDB.

    Implementation notes:
    - The agentic-service writes items with PK course_id and a normal attribute user_id.
    - Without a GSI on user_id, we must Scan + FilterExpression. For expected small cardinality per user, this is acceptable.
    - If a GSI becomes available, this function can be switched to a Query.
    """
    table = _ddb_table()
    if table is None:
        return None
    try:
        from boto3.dynamodb.conditions import Attr

        items: List[Dict[str, Any]] = []
        scan_kwargs = {"FilterExpression": Attr("user_id").eq(str(user_id))}
        resp = table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []) or [])
        # Handle pagination
        while "LastEvaluatedKey" in resp:
            resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"], **scan_kwargs)
            items.extend(resp.get("Items", []) or [])

        # Normalize a subset of fields for frontend
        normalized: List[Dict[str, Any]] = []
        for it in items:
            normalized.append(
                {
                    "course_id": it.get("course_id"),
                    "user_id": it.get("user_id"),
                    "title": it.get("title"),
                    "description": it.get("description"),
                    "progress": it.get("progress"),
                    "title_ready": bool(it.get("title_ready", False)),
                    "lessons_ready": bool(it.get("lessons_ready", False)),
                    "final_ready": bool(it.get("final_ready", False)),
                    "vectorized": bool(it.get("vectorized", False)),
                    "lessons_count": it.get("lessons_count"),
                    "lessons_planned": it.get("lessons_planned"),
                    "roadmap_count": it.get("roadmap_count"),
                    "updated_at": it.get("updated_at"),
                }
            )
        return normalized
    except (ClientError, BotoCoreError) as e:
        logger.error("DynamoDB scan error: %s", e)
        return None
