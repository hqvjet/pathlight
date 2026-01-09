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
        
        # Extract status fields
        vectorization_status = "done" if bool(item.get("vectorized", False)) else "pending"
        planning_status = "done" if bool(item.get("title_ready", False)) else "pending"
        lessons_status = "done" if bool(item.get("lessons_ready", False)) else "pending"
        tests_status = "done" if bool(item.get("tests_ready", False)) else "pending"
        
        # Calculate overall status
        all_done = (
            vectorization_status == "done" and
            planning_status == "done" and
            lessons_status == "done" and
            tests_status == "done"
        )
        overall_status = "done" if all_done else "processing"
        if item.get("error_message"):
            overall_status = "error"
        
        # Build lessons list
        lessons_list = []
        lessons_completed = 0
        lessons_total = item.get("lessons_count") or item.get("roadmap_count") or 0
        
        if item.get("lessons_data"):
            for lesson in item.get("lessons_data", []):
                lessons_list.append({
                    "id": lesson.get("id", ""),
                    "title": lesson.get("title", "")
                })
                if lesson.get("completed"):
                    lessons_completed += 1
        else:
            lessons_completed = lessons_total if lessons_status == "done" else 0
        
        return {
            "overall_status": overall_status,
            "error_message": item.get("error_message", ""),
            
            "vectorization_status": vectorization_status,
            "vectorization_chunks": item.get("vectorization_chunks", 0),
            
            "planning_status": planning_status,
            "planning_course_title": item.get("title", ""),
            "planning_roadmap_count": item.get("roadmap_count", 0),
            
            "lessons_status": lessons_status,
            "lessons_completed": lessons_completed,
            "lessons_total": lessons_total,
            "lessons_list": lessons_list,
            
            "tests_status": tests_status,
            "tests_completed": lessons_total if tests_status == "done" else 0,
            "tests_total": lessons_total,
            
            "start_timestamp": item.get("start_timestamp"),
            "updated_at": item.get("updated_at"),
            "last_updated": item.get("updated_at"),
            "end_timestamp": item.get("end_timestamp"),
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
            # Extract status fields
            vectorization_status = "done" if bool(it.get("vectorized", False)) else "pending"
            planning_status = "done" if bool(it.get("title_ready", False)) else "pending"
            lessons_status = "done" if bool(it.get("lessons_ready", False)) else "pending"
            tests_status = "done" if bool(it.get("tests_ready", False)) else "pending"
            
            # Calculate overall status
            all_done = (
                vectorization_status == "done" and
                planning_status == "done" and
                lessons_status == "done" and
                tests_status == "done"
            )
            overall_status = "done" if all_done else "processing"
            if it.get("error_message"):
                overall_status = "error"
            
            # Build lessons list
            lessons_list = []
            lessons_completed = 0
            lessons_total = it.get("lessons_count") or it.get("roadmap_count") or 0
            
            if it.get("lessons_data"):
                for lesson in it.get("lessons_data", []):
                    lessons_list.append({
                        "id": lesson.get("id", ""),
                        "title": lesson.get("title", "")
                    })
                    if lesson.get("completed"):
                        lessons_completed += 1
            else:
                lessons_completed = lessons_total if lessons_status == "done" else 0
            
            normalized.append({
                "course_id": it.get("course_id"),
                "user_id": it.get("user_id"),
                "overall_status": overall_status,
                "error_message": it.get("error_message", ""),
                
                "vectorization_status": vectorization_status,
                "vectorization_chunks": it.get("vectorization_chunks", 0),
                
                "planning_status": planning_status,
                "planning_course_title": it.get("title", ""),
                "planning_roadmap_count": it.get("roadmap_count", 0),
                
                "lessons_status": lessons_status,
                "lessons_completed": lessons_completed,
                "lessons_total": lessons_total,
                "lessons_list": lessons_list,
                
                "tests_status": tests_status,
                "tests_completed": lessons_total if tests_status == "done" else 0,
                "tests_total": lessons_total,
                
                "start_timestamp": it.get("start_timestamp"),
                "updated_at": it.get("updated_at"),
                "last_updated": it.get("updated_at"),
                "end_timestamp": it.get("end_timestamp"),
            })
        return normalized
    except (ClientError, BotoCoreError) as e:
        logger.error("DynamoDB scan error: %s", e)
        return None
