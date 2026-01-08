import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import boto3


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session(region: str | None, profile: str | None = None) -> boto3.Session:
    if profile:
        return boto3.Session(profile_name=profile, region_name=region)
    # Support project env var names
    akid = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("ACCESS_KEY_ID")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("SECRET_ACCESS_KEY")
    token = os.getenv("AWS_SESSION_TOKEN") or os.getenv("SESSION_TOKEN")
    if akid and secret:
        return boto3.Session(aws_access_key_id=akid, aws_secret_access_key=secret, aws_session_token=token, region_name=region)
    return boto3.Session(region_name=region)


def send_generate_with_vectorize(
    queue_url: str,
    course_id: str,
    s3_keys: Optional[List[str]],
    *,
    difficulty: str,
    duration: int,
    user_id: Optional[str] = None,
    region: Optional[str] = None,
    group_id: Optional[str] = None,
    job_type: str = "GENERATE_COURSE_WITH_VECTORIZE",
) -> dict:
    region = region or os.getenv("REGION") or "ap-northeast-1"
    session = _session(region)
    sqs = session.client("sqs", region_name=region)

    payload = {
        "id": course_id,
        "user_id": user_id,
        "difficulty": difficulty,
        "duration": duration,
        "s3_keys": s3_keys or [],
    }

    body = json.dumps(
        {
            "type": job_type,
            "correlation_id": str(uuid.uuid4()),
            "timestamp": _iso_now(),
            "payload": payload,
        }
    )

    params = {"QueueUrl": queue_url, "MessageBody": body}
    if queue_url.endswith(".fifo"):
        params["MessageGroupId"] = group_id or "agentic"
        params["MessageDeduplicationId"] = str(uuid.uuid4())
    return sqs.send_message(**params)


def send_chatbot_question(
    queue_url: str,
    chat_id: Optional[str],
    message: str,
    lesson_id: Optional[str],
    course_id: Optional[str],
    user_id: str,
    chat_history: Optional[list] = None,
    *,
    region: Optional[str] = None,
    group_id: Optional[str] = None,
) -> dict:
    """
    Send chatbot question to SQS for asynchronous processing.
    
    Args:
        queue_url: SQS queue URL
        chat_id: Chat session ID (optional)
        message: User's question
        lesson_id: Lesson ID for context (optional)
        course_id: Course ID (optional)
        user_id: User ID making the request
        chat_history: Previous conversation messages (optional)
        region: AWS region
        group_id: Message group ID for FIFO queues
        
    Returns:
        SQS send_message response
    """
    region = region or os.getenv("REGION") or "ap-northeast-1"
    session = _session(region)
    sqs = session.client("sqs", region_name=region)

    payload = {
        "chat_id": chat_id,
        "message": message,
        "lesson_id": lesson_id,
        "course_id": course_id,
        "user_id": user_id,
        "chat_history": chat_history or [],
    }

    body = json.dumps(
        {
            "type": "CHATBOT_QUESTION",
            "correlation_id": str(uuid.uuid4()),
            "timestamp": _iso_now(),
            "payload": payload,
        }
    )

    params = {"QueueUrl": queue_url, "MessageBody": body}
    if queue_url.endswith(".fifo"):
        params["MessageGroupId"] = group_id or "chatbot"
        params["MessageDeduplicationId"] = str(uuid.uuid4())
    return sqs.send_message(**params)


def send_recommend_courses(
    queue_url: str,
    sim_id: str,
    user_id: str,
    course_ids: List[str],
    topk: int = 20,
    *,
    region: Optional[str] = None,
    group_id: Optional[str] = None,
) -> dict:
    """
    Send RECOMMEND_COURSES message to SQS.
    
    Args:
        queue_url: SQS queue URL
        sim_id: Unique similarity search ID
        user_id: User ID for profile-based recommendation
        course_ids: List of candidate course IDs (all public courses)
        topk: Number of recommendations to return
        region: AWS region
        group_id: Message group ID for FIFO queues
        
    Returns:
        SQS send_message response
    """
    region = region or os.getenv("REGION") or "ap-northeast-1"
    session = _session(region)
    sqs = session.client("sqs", region_name=region)

    payload = {
        "sim_id": sim_id,
        "user_id": user_id,
        "topk": topk,
        "course_ids": course_ids,
    }

    body = json.dumps(
        {
            "type": "RECOMMEND_COURSES",
            "correlation_id": str(uuid.uuid4()),
            "timestamp": _iso_now(),
            "payload": payload,
        }
    )

    params = {"QueueUrl": queue_url, "MessageBody": body}
    if queue_url.endswith(".fifo"):
        params["MessageGroupId"] = group_id or "agentic"
        params["MessageDeduplicationId"] = str(uuid.uuid4())
    return sqs.send_message(**params)


