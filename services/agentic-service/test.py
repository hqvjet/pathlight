#!/usr/bin/env python3
"""
Quick SQS producer to test the Agentic Service Lambda trigger.

Usage examples:
    python test.py --queue-url https://sqs.ap-northeast-1.amazonaws.com/123456789012/pathlight-agentic-queue.fifo \
        --type generate_course --id course-42 --difficulty medium --duration 1200 --group-id agentic

    python test.py --queue-url https://sqs.ap-northeast-1.amazonaws.com/123456789012/pathlight-agentic-queue.fifo \
        --type vectorize --material-id course-42 --category 0 --s3-key docs/intro.pdf --s3-key docs/overview.docx --group-id agentic

Environment:
    - AWS creds via environment/profile
    - REGION optional (defaults to ap-northeast-1)
    - SQS_QUEUE_URL optional alternative to --queue-url

Notes:
    - This script loads .env by default but DOES NOT override existing process env vars.
        If your .env has stale AWS keys, your shell env or profile will still win.
        Use --dotenv 0 to skip loading .env entirely.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
import re
from dotenv import load_dotenv, find_dotenv

# Load .env if present, but do NOT override shell env (avoid stomping valid AWS creds)
_dotenv_path = find_dotenv(usecwd=True)
if _dotenv_path:
    load_dotenv(_dotenv_path, override=False)

import boto3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(SCRIPT_DIR, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from contracts.sqs_contracts import (
    MessageType,
    VectorizeMessage,
    GenerateCourseMessage,
)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_generate_course(args) -> str:
    msg = GenerateCourseMessage(
        type=MessageType.GENERATE_COURSE,
        correlation_id=str(uuid.uuid4()),
        timestamp=iso_now(),
        payload={
            "id": args.id,
            "difficulty": args.difficulty,
            "duration": args.duration,
        },
    )
    return msg.model_dump_json()


def build_vectorize(args) -> str:
    msg = VectorizeMessage(
        type=MessageType.VECTORIZE_MATERIAL,
        correlation_id=str(uuid.uuid4()),
        timestamp=iso_now(),
        payload={
            "material_id": args.material_id,
            "category": args.category,
            "s3_keys": args.s3_key or [],
        },
    )
    return msg.model_dump_json()


def _parse_queue_region(queue_url: str) -> str | None:
    # Expected: https://sqs.<region>.amazonaws.com/<account>/<name>
    try:
        m = re.match(r"^https://sqs\.([a-z0-9-]+)\.amazonaws\.com/\d+/.+", queue_url)
        return m.group(1) if m else None
    except Exception:
        return None


def _make_boto3_session(region: str, profile: str | None):
    """Create a boto3 Session preferring --profile, falling back to ACCESS_KEY_ID/SECRET_ACCESS_KEY, then default chain."""
    # 1) Named profile
    if profile:
        return boto3.Session(profile_name=profile, region_name=region)

    # 2) Custom env var names used in project
    akid = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("ACCESS_KEY_ID")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("SECRET_ACCESS_KEY")
    token = os.getenv("AWS_SESSION_TOKEN") or os.getenv("SESSION_TOKEN")
    if akid and secret:
        return boto3.Session(
            aws_access_key_id=akid,
            aws_secret_access_key=secret,
            aws_session_token=token,
            region_name=region,
        )

    # 3) Default provider chain (env, container, IAM role, SSO/profile defaults)
    return boto3.Session(region_name=region)


def _print_credential_diagnostics(session: boto3.Session, region: str, profile: str | None, queue_url: str):
    # Credential source and last4 for quick sanity (do not print full keys)
    try:
        creds = session.get_credentials()
        method = getattr(creds, "method", "unknown") if creds else None
        frozen = creds.get_frozen_credentials() if creds else None
        akid = getattr(frozen, "access_key", None)
        last4 = akid[-4:] if akid else "None"
        print(f"Credential source: method={method}, access_key_last4={last4}, region={region}, profile={profile or os.getenv('AWS_PROFILE') or 'default'}")
        # Detect temp creds missing session token (common cause of InvalidClientTokenId)
        env_token = os.getenv("AWS_SESSION_TOKEN") or os.getenv("SESSION_TOKEN")
        has_runtime_token = getattr(frozen, "token", None) is not None
        if akid and akid.startswith("ASIA") and not (env_token or has_runtime_token):
            print("Warning: Access key looks like temporary credentials (ASIA...) but no session token detected. Set AWS_SESSION_TOKEN.")
    except Exception as e:
        print(f"Credential inspection failed: {e}")

    # Show parsed queue account and region
    try:
        m = re.match(r"^https://sqs\.([a-z0-9-]+)\.amazonaws\.com/(\d+)/.+", queue_url)
        if m:
            q_region, q_acct = m.group(1), m.group(2)
            print(f"Target queue: region={q_region}, account={q_acct}")
    except Exception:
        pass


def send_message(queue_url: str, region: str, body: str, group_id: str | None = None, profile: str | None = None, skip_sts: bool = False):
    session = _make_boto3_session(region, profile)
    _print_credential_diagnostics(session, region, profile, queue_url)
    # Preflight: whoami
    if not skip_sts:
        try:
            sts = session.client("sts", region_name=region)
            ident = sts.get_caller_identity()
            print(f"Using AWS identity: {ident.get('Arn')} (Account: {ident.get('Account')}) in {region}")
        except Exception as e:
            print("Failed to get STS identity with provided credentials.")
            print(f"Error: {e}")
            print("\nTroubleshooting checklist:")
            print("  1) If using temporary credentials, ensure AWS_SESSION_TOKEN is set alongside AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY.")
            print("  2) If using a profile, pass --profile <name> and verify with: aws sts get-caller-identity --profile <name>.")
            print("  3) Ensure the credentials are for the same AWS account as the queue's account (see 'Target queue' above).")
            print("  4) Check that .env isn't overriding creds; this script does NOT override shell env, but verify your shell vars.")
            print("  5) If using SSO, ensure you've run: aws sso login --profile <name>.")
            sys.exit(1)
    sqs = session.client("sqs", region_name=region)
    params = {"QueueUrl": queue_url, "MessageBody": body}
    if queue_url.endswith(".fifo"):
        params["MessageGroupId"] = group_id or "agentic"
        # Using a random dedup id each time to ensure processing for tests
        params["MessageDeduplicationId"] = str(uuid.uuid4())
    resp = sqs.send_message(**params)
    return resp


def parse_args():
    p = argparse.ArgumentParser(description="Send a test message to the Agentic Service SQS queue")
    p.add_argument("--queue-url", default=os.getenv("SQS_QUEUE_URL"), help="SQS queue URL")
    p.add_argument("--region", default=os.getenv("REGION"), help="AWS region (auto-detected from queue URL if omitted)")
    p.add_argument("--group-id", default=os.getenv("SQS_GROUP_ID"), help="FIFO MessageGroupId (if queue is .fifo)")
    p.add_argument("--profile", default=os.getenv("AWS_PROFILE"), help="AWS named profile to use")
    p.add_argument("--skip-sts", action="store_true", help="Skip STS preflight identity check")
    p.add_argument("--dotenv", type=int, choices=[0,1], default=1, help="Load .env (1) or skip (0)")
    p.add_argument("--type", choices=["generate_course", "vectorize"], default="generate_course")

    # generate_course
    p.add_argument("--id", help="Course ID (generate_course)")
    p.add_argument("--difficulty", default="medium", help="Course difficulty")
    p.add_argument("--duration", type=int, default=1200, help="Course duration in seconds")

    # vectorize
    p.add_argument("--material-id", help="Material ID (vectorize)")
    p.add_argument("--category", type=int, default=0, help="Category, 0=course, 1=quiz")
    p.add_argument("--s3-key", action="append", help="S3 key to vectorize (repeat flag)")
    return p.parse_args()


def main():
    args = parse_args()
    # Optionally skip .env loading if requested (env already loaded above by default)
    if args.dotenv == 0:
        # Best-effort: re-exec without .env by unsetting typical vars; simpler: warn user
        print("Skipping .env as requested (--dotenv 0). If already loaded earlier, please unset in shell if needed.")
    if not args.queue_url:
        print("SQS queue URL is required (set --queue-url or env SQS_QUEUE_URL)")
        sys.exit(2)

    # Prefer region from URL if not provided or mismatched
    url_region = _parse_queue_region(args.queue_url)
    effective_region = args.region or url_region or "ap-northeast-1"
    if args.region and url_region and args.region != url_region:
        print(f"Warning: --region {args.region} != URL region {url_region}; using {url_region}")
        effective_region = url_region

    if args.type == "generate_course":
        if not args.id:
            print("--id is required for generate_course")
            sys.exit(2)
        body = build_generate_course(args)
    else:
        if not args.material_id or not args.s3_key:
            print("--material-id and at least one --s3-key are required for vectorize")
            sys.exit(2)
        body = build_vectorize(args)

    resp = send_message(args.queue_url, effective_region, body, args.group_id, args.profile, skip_sts=args.skip_sts)
    print("Sent message:\n", json.dumps(json.loads(body), indent=2))
    print("SQS response:\n", json.dumps(resp, default=str, indent=2))


if __name__ == "__main__":
    main()
