"""Minimal DynamoDB client wrapper used for generation status tracking.

Best-effort: all operations swallow AWS errors and log a warning so the
agentic pipeline never fails due to tracking.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from core.logging import setup_logger


logger = setup_logger(__name__)


def _table_name() -> str:
    return os.getenv("DDB_TABLE_NAME", "pathlight-agentic-status")


def _resource():
    region = os.getenv("REGION", "ap-northeast-1")
    access_key = os.getenv("ACCESS_KEY_ID")
    secret_key = os.getenv("SECRET_ACCESS_KEY")
    try:
        if access_key and secret_key:
            return boto3.resource(
                "dynamodb", region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key
            )
        return boto3.resource("dynamodb", region_name=region)
    except Exception as e:
        logger.warning(f"DynamoDB resource init failed: {e}")
        return None


def _ensure_table(resource) -> Optional[Any]:
    name = _table_name()
    if resource is None:
        return None
    try:
        table = resource.Table(name)
        # A light touch to force describe and catch non-existence
        table.load()
        return table
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code != "ResourceNotFoundException":
            logger.warning(f"DynamoDB describe_table failed: {e}")
            return None

    # Auto-create only if explicitly enabled
    if os.getenv("DDB_AUTO_CREATE_TABLE", "false").lower() == "true":
        try:
            table = resource.create_table(
                TableName=name,
                KeySchema=[{"AttributeName": "course_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "course_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
            table.wait_until_exists()
            logger.info(f"Created DynamoDB table {name}")
            return table
        except Exception as e:
            logger.warning(f"Failed to create DynamoDB table {name}: {e}")
            return None
    else:
        logger.warning(
            f"DynamoDB table {name} not found and auto-create disabled; tracking will be skipped."
        )
        return None


def put_item(item: Dict[str, Any]) -> None:
    resource = _resource()
    table = _ensure_table(resource) if resource else None
    if not table:
        return
    try:
        item["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        table.put_item(Item=item)
    except (ClientError, BotoCoreError) as e:
        logger.warning(f"DynamoDB put_item failed: {e}")


def ensure_table(strict: bool = False) -> bool:
    """Ensure DynamoDB table exists; optionally raise if unavailable.

    Returns True if table is available, False otherwise. If strict=True and table
    is not available, raises a RuntimeError.
    """
    resource = _resource()
    table = _ensure_table(resource) if resource else None
    ok = table is not None
    if not ok and strict:
        raise RuntimeError(
            f"DynamoDB table {_table_name()} unavailable and auto-create disabled"
        )
    return ok


def put_item_strict(item: Dict[str, Any]) -> None:
    """Strict variant of put_item: raises if table unavailable or write fails."""
    resource = _resource()
    table = _ensure_table(resource) if resource else None
    if not table:
        raise RuntimeError(
            f"DynamoDB table {_table_name()} unavailable; cannot create status item"
        )
    try:
        item["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        table.put_item(Item=item)
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"DynamoDB put_item failed: {e}")


def update_item(course_id: str, updates: Dict[str, Any]) -> None:
    resource = _resource()
    table = _ensure_table(resource) if resource else None
    if not table:
        return
    try:
        # Simple upsert/merge pattern: read, shallow-merge, write back
        current = {}
        try:
            resp = table.get_item(Key={"course_id": course_id})
            current = resp.get("Item", {}) or {}
        except Exception:
            current = {"course_id": course_id}
        current.update(updates)
        put_item(current)
    except (ClientError, BotoCoreError) as e:
        logger.warning(f"DynamoDB update_item failed: {e}")
