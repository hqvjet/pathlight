import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, Sequence
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import config
from schemas.user_schemas import AdminLogsResponse, AdminLogItem

logger = logging.getLogger(__name__)

Vietnam_TZ = timezone(timedelta(hours=7))

FilterKey = Literal["daily", "weekly", "monthly", "hourly", "30m", "1m"]

_FILTER_TO_WINDOW = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
    "hourly": timedelta(hours=1),
    "30m": timedelta(minutes=30),
    "1m": timedelta(minutes=1),
}

_LOG_LEVEL_PREFIXES = ["ERROR", "WARN", "WARNING", "INFO", "DEBUG"]

# Default log groups for the Pathlight stack (can be overridden via env CLOUDWATCH_LOG_GROUP_NAME_LIST)
_DEFAULT_LOG_GROUPS = [
    "/aws/lambda/pathlight-agentic-service",
    "/aws/lambda/pathlight-authentication-service",
    "/aws/lambda/pathlight-course-service",
    "/aws/lambda/pathlight-user-service",
    "/aws/lambda/pathlight-quiz-service",
]

def _resolve_log_groups(selected: str | None) -> list[str]:
    """Return the list of log groups to query.

    - If `selected` is provided, validate it is one of the known groups.
    - Else, use env CLOUDWATCH_LOG_GROUP_NAME_LIST (comma-separated) or the default list above.
    - For backward compatibility, if CLOUDWATCH_LOG_GROUP_NAME is set and list is empty, use it.
    """
    env_list = os.getenv("CLOUDWATCH_LOG_GROUP_NAME_LIST")
    groups_env = []
    if env_list:
        groups_env = [g.strip() for g in env_list.split(",") if g.strip()]

    if selected:
        if selected == "all":
            return groups_env or _DEFAULT_LOG_GROUPS
        # Allow either full name or short suffix match (last token)
        candidates = groups_env or _DEFAULT_LOG_GROUPS
        if selected in candidates:
            return [selected]
        # try suffix match
        for g in candidates:
            if g.rsplit("/", 1)[-1] == selected:
                return [g]
        return []

    if groups_env:
        return groups_env

    if config.CLOUDWATCH_LOG_GROUP_NAME:
        return [config.CLOUDWATCH_LOG_GROUP_NAME]

    return _DEFAULT_LOG_GROUPS


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
        if upper_msg.startswith(prefix) or upper_msg.startswith(f"[{prefix}]"):
            return "WARN" if prefix == "WARNING" else prefix

    match = re.search(r"\b(ERROR|WARN|WARNING|INFO|DEBUG)\b", upper_msg)
    if match:
        value = match.group(1)
        return "WARN" if value == "WARNING" else value

    return "INFO"


def _format_events(events: Sequence[dict], source: str) -> list[AdminLogItem]:
    formatted: list[AdminLogItem] = []
    for event in events:
        message = (event.get("message") or "").rstrip()
        formatted.append(
            AdminLogItem(
                timestamp=_to_vietnam_time(int(event.get("timestamp", 0))),
                type=_detect_log_level(message),
                log=message,
                source=source,
            )
        )
    return formatted


def get_admin_logs(filter_key: FilterKey, *, service: Optional[str] = None, logs_client=None) -> AdminLogsResponse:
    """Fetch logs from CloudWatch for the requested window and convert to VN time.

    - filter_key: daily | weekly | monthly
    - service: optional specific log group (full name or suffix). If None, aggregate all known groups.
    """
    if filter_key not in _FILTER_TO_WINDOW:
        allowed = ", ".join(_FILTER_TO_WINDOW.keys())
        return AdminLogsResponse(status=400, message=f"filter must be one of: {allowed}", logs=[])

    log_groups = _resolve_log_groups(service)
    if not log_groups:
        return AdminLogsResponse(status=400, message="Log group không hợp lệ", logs=[])

    start_time, end_time = _resolve_time_window(filter_key)  # UTC datetimes
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    client = logs_client or boto3.client(
        "logs",
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY or None,
    )

    formatted: list[AdminLogItem] = []

    for group in log_groups:
        events: list[dict] = []
        next_token: Optional[str] = None
        try:
            while True:
                params = {
                    "logGroupName": group,
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
            logger.error(f"Failed to fetch CloudWatch logs for {group}: {exc}")
            return AdminLogsResponse(status=502, message="Không thể lấy log từ CloudWatch", logs=[])
        except Exception as exc:  # pragma: no cover - safety net
            logger.error(f"Unexpected error while fetching logs for {group}: {exc}")
            return AdminLogsResponse(status=500, message="Có lỗi xảy ra khi lấy log", logs=[])

        events.sort(key=lambda e: e.get("timestamp", 0))
        formatted.extend(_format_events(events, source=group))

    # Sort combined logs by timestamp
    formatted.sort(key=lambda e: e.timestamp)
    return AdminLogsResponse(status=200, logs=formatted)
