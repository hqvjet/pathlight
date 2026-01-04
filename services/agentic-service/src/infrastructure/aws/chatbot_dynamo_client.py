"""DynamoDB client for chatbot conversation tracking.

Manages chat messages, responses, and statuses in the chatbot_table.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from core.logging import setup_logger


logger = setup_logger(__name__)


class ChatStatus(str, Enum):
    """Chat message status."""
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


def _table_name() -> str:
    """Get chatbot table name from environment."""
    return os.getenv("CHATBOT_DDB_TABLE_NAME", "chatbot_table")


def _resource():
    """Create DynamoDB resource."""
    region = os.getenv("REGION", "ap-northeast-1")
    access_key = os.getenv("ACCESS_KEY_ID")
    secret_key = os.getenv("SECRET_ACCESS_KEY")
    try:
        if access_key and secret_key:
            return boto3.resource(
                "dynamodb", 
                region_name=region, 
                aws_access_key_id=access_key, 
                aws_secret_access_key=secret_key
            )
        return boto3.resource("dynamodb", region_name=region)
    except Exception as e:
        logger.warning(f"DynamoDB resource init failed: {e}")
        return None


def _ensure_table(resource) -> Optional[Any]:
    """Ensure chatbot table exists, create if needed."""
    name = _table_name()
    if resource is None:
        return None
    try:
        table = resource.Table(name)
        table.load()
        return table
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code != "ResourceNotFoundException":
            logger.warning(f"DynamoDB describe_table failed: {e}")
            return None

    # Auto-create table if enabled
    if os.getenv("DDB_AUTO_CREATE_TABLE", "false").lower() == "true":
        try:
            table = resource.create_table(
                TableName=name,
                KeySchema=[{"AttributeName": "chat_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "chat_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
            table.wait_until_exists()
            logger.info(f"Created DynamoDB chatbot table {name}")
            return table
        except Exception as e:
            logger.warning(f"Failed to create DynamoDB table {name}: {e}")
            return None
    else:
        logger.warning(
            f"DynamoDB table {name} not found and auto-create disabled"
        )
        return None


def create_chat_record(
    chat_id: str,
    message: str,
    lesson_id: str,
    course_id: str,
    user_id: str,
) -> bool:
    """Create initial chat record with processing status.
    
    Args:
        chat_id: Unique chat identifier
        message: User's question
        lesson_id: Lesson identifier
        course_id: Course identifier
        user_id: User identifier
        
    Returns:
        True if successful, False otherwise
    """
    resource = _resource()
    table = _ensure_table(resource) if resource else None
    if not table:
        logger.warning("DynamoDB table not available - chat record creation skipped")
        return False
    
    try:
        item = {
            "chat_id": chat_id,
            "message": message,
            "lesson_id": lesson_id,
            "course_id": course_id,
            "user_id": user_id,
            "status": ChatStatus.PROCESSING.value,
            "response": "",
            "error_message": "",
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        table.put_item(Item=item)
        logger.info(f"Created chat record: chat_id={chat_id}, status=processing")
        return True
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to create chat record: {e}")
        return False


def update_chat_status(
    chat_id: str,
    status: ChatStatus,
    response: str = "",
    error_message: str = "",
    context_chunks: Optional[list] = None,
) -> bool:
    """Update chat record with final status and response.
    
    Args:
        chat_id: Chat identifier
        status: Final status (done or error)
        response: Bot's response text
        error_message: Error message if status is error
        context_chunks: Retrieved context chunks used for response
        
    Returns:
        True if successful, False otherwise
    """
    resource = _resource()
    table = _ensure_table(resource) if resource else None
    if not table:
        logger.warning("DynamoDB table not available - chat update skipped")
        return False
    
    try:
        update_expr = "SET #status = :status, #response = :response, #updated_at = :updated_at"
        expr_attr_names = {
            "#status": "status",
            "#response": "response",
            "#updated_at": "updated_at",
        }
        expr_attr_values = {
            ":status": status.value,
            ":response": response,
            ":updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        
        if error_message:
            update_expr += ", #error_message = :error_message"
            expr_attr_names["#error_message"] = "error_message"
            expr_attr_values[":error_message"] = error_message
        
        if context_chunks:
            update_expr += ", #context_chunks = :context_chunks"
            expr_attr_names["#context_chunks"] = "context_chunks"
            expr_attr_values[":context_chunks"] = context_chunks
        
        table.update_item(
            Key={"chat_id": chat_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
        )
        logger.info(f"Updated chat record: chat_id={chat_id}, status={status.value}")
        return True
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to update chat record: {e}")
        return False


def get_chat_record(chat_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve chat record by chat_id.
    
    Args:
        chat_id: Chat identifier
        
    Returns:
        Chat record dict or None if not found
    """
    resource = _resource()
    table = _ensure_table(resource) if resource else None
    if not table:
        return None
    
    try:
        response = table.get_item(Key={"chat_id": chat_id})
        return response.get("Item")
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to get chat record: {e}")
        return None
