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
    quiz_id: str,
    s3_keys: Optional[List[str]],
    *,
    difficulty: str,
    duration: int,
    user_id: Optional[str] = None,
    region: Optional[str] = None,
    group_id: Optional[str] = None,
    job_type: str = "GENERATE_QUIZ_WITH_VECTORIZE",
    num_questions: Optional[int] = None,
) -> dict:
    region = region or os.getenv("REGION") or "ap-northeast-1"
    session = _session(region)
    sqs = session.client("sqs", region_name=region)

    # Build payload based on job type
    if job_type == "GENERATE_QUIZ_WITH_VECTORIZE":
        payload = {
            "id": quiz_id,
            "user_id": user_id,
            "difficulty": difficulty,
            "duration": duration,
            "num_questions": num_questions or 10,
            "s3_keys": s3_keys or [],
        }
    else:
        # Quiz format: keep existing fields for backward compatibility
        payload = {
            "id": quiz_id,
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
