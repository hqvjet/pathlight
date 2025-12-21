"""
Status tracking service for quiz generation using DynamoDB.
"""
import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

_ddb_table_instance: Optional[Any] = None


def _ddb_table():
    """Return a cached DynamoDB Table resource for quiz generation status.
    
    Uses DYNAMODB_TABLE_NAME from environment (should be same as course service).
    Returns None if boto3 is unavailable or table name not configured.
    """
    global _ddb_table_instance
    if _ddb_table_instance is not None:
        return _ddb_table_instance
    
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    if not table_name:
        logger.warning("DYNAMODB_TABLE_NAME not set; generation status unavailable")
        return None
    
    try:
        import boto3
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.getenv("REGION", "ap-northeast-1"),
        )
        _ddb_table_instance = dynamodb.Table(table_name)  # type: ignore[attr-defined]
        return _ddb_table_instance
    except ImportError:
        logger.warning("boto3 not installed; generation status unavailable")
        return None
    except Exception as e:
        logger.error("Failed to initialize DynamoDB table: %s", e)
        return None


def fetch_generation_status(quiz_id: str) -> Optional[Dict[str, Any]]:
    """Fetch and normalize generation status for a quiz from DynamoDB.

    Returns None when not found or on error.
    
    Expected DynamoDB item structure:
    - PK: course_id (yes, same table as courses, but quiz uses quiz_id)
    - title_ready: bool
    - cards_ready: bool (instead of lessons_ready)
    - final_ready: bool
    - vectorized: bool
    - progress: str
    - updated_at: str
    - user_id: str
    """
    table = _ddb_table()
    if table is None:
        return None
    
    try:
        # DynamoDB uses "course_id" as PK, so we query with quiz_id as the key
        resp = table.get_item(Key={"course_id": quiz_id})
        item = resp.get("Item")
        if not item:
            return None
        
        title_ready = bool(item.get("title_ready", False))
        cards_ready = bool(item.get("cards_ready", False))
        final_ready = bool(item.get("final_ready", False))
        vectorized = bool(item.get("vectorized", False))
        overall = title_ready and cards_ready and final_ready
        
        return {
            "status": overall,
            "vectorized": vectorized,
            "title_ready": title_ready,
            "cards_ready": cards_ready,
            "final_ready": final_ready,
            "progress": item.get("progress"),
            "updated_at": item.get("updated_at"),
        }
    except Exception as e:
        logger.error("DynamoDB get_item error for quiz %s: %s", quiz_id, e)
        return None


def fetch_user_quiz_generations(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Return all quiz generation rows for the given user_id from DynamoDB.

    Implementation notes:
    - Scans DynamoDB table filtering by user_id
    - Returns normalized quiz generation items
    - Filters out course items by checking for 'quiz' prefix in course_id
    """
    table = _ddb_table()
    if table is None:
        return None
    
    try:
        from boto3.dynamodb.conditions import Attr

        items: List[Dict[str, Any]] = []
        # Scan with filter for user_id
        scan_kwargs = {"FilterExpression": Attr("user_id").eq(str(user_id))}
        resp = table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []) or [])
        
        # Handle pagination
        while "LastEvaluatedKey" in resp:
            resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"], **scan_kwargs)
            items.extend(resp.get("Items", []) or [])

        # Filter for quiz items only (course_id starts with "quiz-")
        quiz_items = [it for it in items if str(it.get("course_id", "")).startswith("quiz-")]

        # Normalize fields for frontend
        normalized: List[Dict[str, Any]] = []
        for it in quiz_items:
            normalized.append({
                "quiz_id": it.get("course_id"),  # The PK is stored as course_id
                "user_id": it.get("user_id"),
                "progress": it.get("progress"),
                "title_ready": bool(it.get("title_ready", False)),
                "cards_ready": bool(it.get("cards_ready", False)),
                "final_ready": bool(it.get("final_ready", False)),
                "vectorized": bool(it.get("vectorized", False)),
                "updated_at": it.get("updated_at"),
            })
        
        return normalized
    except Exception as e:
        logger.error("DynamoDB scan error for user %s quizzes: %s", user_id, e)
        return None
