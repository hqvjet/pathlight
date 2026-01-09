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
    
    Uses DDB_QUIZ_TABLE_NAME from environment (quiz_generation_tracking).
    Returns None if boto3 is unavailable or table name not configured.
    """
    global _ddb_table_instance
    if _ddb_table_instance is not None:
        return _ddb_table_instance
    
    table_name = os.getenv("DDB_QUIZ_TABLE_NAME", "quiz_generation_tracking")
    logger.info(f"Initializing DynamoDB table: {table_name}")
    
    if not table_name:
        logger.warning("DDB_QUIZ_TABLE_NAME not set; generation status unavailable")
        return None
    
    try:
        import boto3
        region = os.getenv("REGION", "ap-northeast-1")
        logger.info(f"Connecting to DynamoDB in region: {region}")
        
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=region,
        )
        _ddb_table_instance = dynamodb.Table(table_name)  # type: ignore[attr-defined]
        logger.info(f"Successfully initialized DynamoDB table: {table_name}")
        return _ddb_table_instance
    except ImportError:
        logger.warning("boto3 not installed; generation status unavailable")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB table {table_name}: {e}", exc_info=True)
        return None


def fetch_generation_status(quiz_id: str) -> Optional[Dict[str, Any]]:
    """Fetch and normalize generation status for a quiz from DynamoDB.

    Returns None when not found or on error.
    
    Expected DynamoDB item structure:
    - PK: quiz_id (primary key for quiz_generation_tracking table)
    - title_ready: bool or plan_ready: bool
    - cards_ready: bool or questions_ready: bool
    - final_ready: bool
    - status: str (initializing, planning, creating_questions, finalizing, completed, failed)
    - progress_percentage: int (0-100)
    - current_step: str
    - current_step_detail: str
    - updated_at: str
    - user_id: str
    """
    table = _ddb_table()
    if table is None:
        return None
    
    try:
        # Use quiz_id as the primary key
        resp = table.get_item(Key={"quiz_id": quiz_id})
        item = resp.get("Item")
        if not item:
            return None
        
        # Check both old and new field names for compatibility
        vectorized = bool(item.get("vectorized", False))
        plan_ready = bool(item.get("plan_ready", False) or item.get("title_ready", False))
        questions_ready = bool(item.get("questions_ready", False) or item.get("cards_ready", False))
        
        # If questions started, vectorization must be done
        if questions_ready:
            vectorized = True
        
        # Status from agentic-service tracking
        status = item.get("status", "unknown")
        progress_percentage = int(item.get("progress_percentage", 0))
        
        return {
            "quiz_id": quiz_id,
            "status": status,
            "progress_percentage": progress_percentage,
            "current_step": item.get("current_step"),
            "current_step_detail": item.get("current_step_detail"),
            "vectorized": vectorized,
            "plan_ready": plan_ready,
            "questions_ready": questions_ready,
            "title": item.get("title"),
            "overview": item.get("overview"),
            "ideas_count": item.get("ideas_count"),
            "questions_count": item.get("questions_count"),
            "updated_at": item.get("updated_at"),
            "user_id": item.get("user_id"),
        }
    except Exception as e:
        logger.error("DynamoDB get_item error for quiz %s: %s", quiz_id, e)
        return None


def fetch_user_quiz_generations(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Return all quiz generation rows for the given user_id from DynamoDB.

    Implementation notes:
    - Scans quiz_generation_tracking table filtering by user_id
    - Returns normalized quiz generation items with status tracking
    """
    logger.info(f"Fetching quiz generations for user_id: {user_id}")
    table = _ddb_table()
    if table is None:
        logger.warning("DynamoDB table not available, returning None")
        return None
    
    try:
        from boto3.dynamodb.conditions import Attr

        items: List[Dict[str, Any]] = []
        # Scan with filter for user_id
        scan_kwargs = {"FilterExpression": Attr("user_id").eq(str(user_id))}
        logger.info(f"Scanning DynamoDB with filter: user_id == {user_id}")
        
        resp = table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []) or [])
        logger.info(f"Found {len(items)} items in first scan")
        
        # Handle pagination
        page_count = 1
        while "LastEvaluatedKey" in resp:
            page_count += 1
            resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"], **scan_kwargs)
            page_items = resp.get("Items", []) or []
            items.extend(page_items)
            logger.info(f"Page {page_count}: Found {len(page_items)} items")

        logger.info(f"Total items found: {len(items)}")

        # Normalize fields for frontend (all items are quizzes in this table)
        normalized: List[Dict[str, Any]] = []
        for it in items:
            vectorized = bool(it.get("vectorized", False))
            plan_ready = bool(it.get("plan_ready", False) or it.get("title_ready", False))
            questions_ready = bool(it.get("questions_ready", False) or it.get("cards_ready", False))
            
            # If questions started, vectorization must be done
            if questions_ready:
                vectorized = True
            
            normalized.append({
                "quiz_id": it.get("quiz_id"),
                "user_id": it.get("user_id"),
                "status": it.get("status", "unknown"),
                "progress_percentage": int(it.get("progress_percentage", 0)),
                "current_step": it.get("current_step"),
                "current_step_detail": it.get("current_step_detail"),
                "vectorized": vectorized,
                "plan_ready": plan_ready,
                "questions_ready": questions_ready,
                "title": it.get("title"),
                "overview": it.get("overview"),
                "ideas_count": it.get("ideas_count"),
                "questions_count": it.get("questions_count"),
                "updated_at": it.get("updated_at"),
            })
        
        logger.info(f"Returning {len(normalized)} normalized items")
        return normalized
    except Exception as e:
        logger.error(f"DynamoDB scan error for user {user_id} quizzes: {e}", exc_info=True)
        return None
