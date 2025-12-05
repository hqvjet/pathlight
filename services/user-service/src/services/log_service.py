import logging
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, Sequence

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import config
from schemas.user_schemas import AdminLogsResponse, AdminLogItem

logger = logging.getLogger(__name__)

Vietnam_TZ = timezone(timedelta(hours=7))

FilterKey = Literal["daily", "weekly", "monthly"]

_FILTER_TO_WINDOW = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}

_LOG_LEVEL_PREFIXES = ["ERROR", "WARN", "WARNING", "INFO", "DEBUG"]


def _resolve_time_window(filter_key: FilterKey) -> tuple[datetime, datetime]:
    """Return UTC start/end datetimes for the requested window."""
    end_time = datetime.now(timezone.utc)
    delta = _FILTER_TO_WINDOW.get(filter_key, timedelta(days=1))
    start_time = end_time - delta
    return start_time, end_time


def _to_vietnam_time(ts_ms: int) -> str:
    utc_dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return utc_dt.astimezone(Vietnam_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _detect_log_level(message: str) -> str:
    upper_msg = message.strip().upper()
    for prefix in _LOG_LEVEL_PREFIXES:
        if upper_msg.startswith(prefix):
            return prefix
    return "INFO"


def _format_events(events: Sequence[dict]) -> list[AdminLogItem]:
    formatted: list[AdminLogItem] = []
    for event in events:
        message = (event.get("message") or "").rstrip()
        formatted.append(
            AdminLogItem(
                timestamp=_to_vietnam_time(int(event.get("timestamp", 0))),
                type=_detect_log_level(message),
                log=message,
            )
        )
    return formatted


def get_admin_logs(filter_key: str, logs_client=None) -> AdminLogsResponse:
    """Fetch logs from CloudWatch for the requested window and convert to VN time."""
    if filter_key not in _FILTER_TO_WINDOW:
        return AdminLogsResponse(status=400, message="filter must be daily, weekly, or monthly", logs=[])

    log_group = config.CLOUDWATCH_LOG_GROUP_NAME
    if not log_group:
        return AdminLogsResponse(status=500, message="CloudWatch log group is not configured", logs=[])

    start_time, end_time = _resolve_time_window(filter_key)  # UTC datetimes
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    client = logs_client or boto3.client(
        "logs",
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY or None,
    )

    events: list[dict] = []
    next_token: Optional[str] = None
    try:
        while True:
            params = {
                "logGroupName": log_group,
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": 1000,
            }
            if next_token:
                params["nextToken"] = next_token
            response = client.filter_log_events(**params)
            events.extend(response.get("events", []))
            new_token = response.get("nextToken")
            if not new_token or new_token == next_token:
                break
            next_token = new_token
    except (ClientError, BotoCoreError) as exc:
        logger.error(f"Failed to fetch CloudWatch logs: {exc}")
        return AdminLogsResponse(status=502, message="Không thể lấy log từ CloudWatch", logs=[])
    except Exception as exc:  # pragma: no cover - safety net
        logger.error(f"Unexpected error while fetching logs: {exc}")
        return AdminLogsResponse(status=500, message="Có lỗi xảy ra khi lấy log", logs=[])

    events.sort(key=lambda e: e.get("timestamp", 0))
    formatted = _format_events(events)
    return AdminLogsResponse(status=200, logs=formatted)
