import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, Sequence
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import config
from schemas.user_schemas import (
    AdminLogsResponse,
    AdminLogItem,
    AdminLogStreamsResponse,
    AdminLogStreamItem,
)

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
_NOISE_PREFIXES = ("START RequestId", "END RequestId", "REPORT RequestId")
_NOISE_PATTERNS = [
    "Lambda Event:",
    '"resource":',
    '"httpMethod":',
    '"queryStringParameters":',
    '"requestContext":',
    "Valid config keys have changed",
    "UserWarning",
    "warnings.warn",
]

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


def _normalize_level(value: str | None) -> str | None:
    if not value:
        return None
    upper = value.strip().upper()
    if upper == "WARNING":
        return "WARN"
    allowed = {"ERROR", "WARN", "INFO", "DEBUG"}
    return upper if upper in allowed else None


def _level_passes_filter(log_type: str, level_filter: str | None) -> bool:
    if not level_filter:
        return True
    weights = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
    return weights.get(log_type.upper(), 1) >= weights.get(level_filter, 1)


def _is_noise_log(message: str) -> bool:
    stripped = (message or "").strip()
    if any(stripped.startswith(prefix) for prefix in _NOISE_PREFIXES):
        return True
    # Filter out verbose Lambda event dumps and framework warnings
    return any(pattern in stripped for pattern in _NOISE_PATTERNS)


def _format_events(events: Sequence[dict], source: str) -> list[AdminLogItem]:
    formatted: list[AdminLogItem] = []
    for event in events:
        message = (event.get("message") or "").rstrip()
        if _is_noise_log(message):
            continue
        formatted.append(
            AdminLogItem(
                timestamp=_to_vietnam_time(int(event.get("timestamp", 0))),
                type=_detect_log_level(message),
                log=message,
                source=source,
            )
        )
    return formatted


def _format_stream_item(stream: dict, log_group: str) -> AdminLogStreamItem:
    last_event_ms = stream.get("lastEventTimestamp")
    last_ingestion_ms = stream.get("lastIngestionTime")
    return AdminLogStreamItem(
        log_group=log_group,
        log_stream=stream.get("logStreamName", ""),
        last_event_time=_to_vietnam_time(last_event_ms) if last_event_ms else None,
        last_ingestion_time=_to_vietnam_time(last_ingestion_ms) if last_ingestion_ms else None,
        stored_bytes=stream.get("storedBytes"),
    )


def list_log_streams(filter_key: FilterKey, *, service: Optional[str] = None, logs_client=None) -> AdminLogStreamsResponse:
    if filter_key not in _FILTER_TO_WINDOW:
        allowed = ", ".join(_FILTER_TO_WINDOW.keys())
        return AdminLogStreamsResponse(status=400, message=f"filter must be one of: {allowed}", streams=[])

    log_groups = _resolve_log_groups(service)
    if not log_groups:
        return AdminLogStreamsResponse(status=400, message="Log group không hợp lệ", streams=[])

    start_time, end_time = _resolve_time_window(filter_key)
    start_ms = int(start_time.timestamp() * 1000)
    _ = end_time  # kept for parity if future filters need upper bound

    client = logs_client or boto3.client(
        "logs",
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY or None,
    )

    items: list[AdminLogStreamItem] = []

    for group in log_groups:
        next_token: Optional[str] = None
        try:
            while True:
                params = {
                    "logGroupName": group,
                    "orderBy": "LastEventTime",
                    "descending": True,
                    "limit": 50,
                }
                if next_token:
                    params["nextToken"] = next_token

                response = client.describe_log_streams(**params)
                for stream in response.get("logStreams", []):
                    last_event_ms = stream.get("lastEventTimestamp")
                    if last_event_ms is not None and last_event_ms < start_ms:
                        continue
                    items.append(_format_stream_item(stream, log_group=group))

                new_token = response.get("nextToken")
                if not new_token or new_token == next_token:
                    break
                next_token = new_token
        except (ClientError, BotoCoreError) as exc:
            logger.error(f"Failed to list CloudWatch log streams for {group}: {exc}")
            return AdminLogStreamsResponse(status=502, message="Không thể lấy log stream từ CloudWatch", streams=[])
        except Exception as exc:  # pragma: no cover - safety net
            logger.error(f"Unexpected error while listing log streams for {group}: {exc}")
            return AdminLogStreamsResponse(status=500, message="Có lỗi xảy ra khi lấy log stream", streams=[])

    # sort by last_event_time desc
    items.sort(key=lambda s: s.last_event_time or "", reverse=True)
    return AdminLogStreamsResponse(status=200, streams=items)


def get_admin_logs(
    filter_key: FilterKey,
    *,
    service: Optional[str] = None,
    log_stream: Optional[str] = None,
    level_filter: Optional[str] = None,
    logs_client=None,
) -> AdminLogsResponse:
    """Fetch logs from CloudWatch for the requested window and convert to VN time.

    - filter_key: daily | weekly | monthly
    - service: optional specific log group (full name or suffix). If None, aggregate all known groups.
    - log_stream: optional specific log stream inside the selected log group. If provided, service must map to a single group.
    """
    if filter_key not in _FILTER_TO_WINDOW:
        allowed = ", ".join(_FILTER_TO_WINDOW.keys())
        return AdminLogsResponse(status=400, message=f"filter must be one of: {allowed}", logs=[])

    log_groups = _resolve_log_groups(service)
    if not log_groups:
        return AdminLogsResponse(status=400, message="Log group không hợp lệ", logs=[])

    if log_stream and len(log_groups) != 1:
        return AdminLogsResponse(status=400, message="Vui lòng chọn 1 dịch vụ khi lấy log theo stream", logs=[])

    start_time, end_time = _resolve_time_window(filter_key)  # UTC datetimes
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    from botocore.config import Config as BotoConfig
    boto_config = BotoConfig(
        connect_timeout=3,
        read_timeout=8,
        retries={'max_attempts': 1}
    )

    client = logs_client or boto3.client(
        "logs",
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY or None,
        config=boto_config,
    )

    formatted: list[AdminLogItem] = []
    normalized_level = _normalize_level(level_filter)

    MAX_ITERATIONS = 2  # Prevent infinite loops - reduced from 5
    MAX_EVENTS_PER_GROUP = 500  # Cap total events to avoid timeout - reduced from 5000

    for group in log_groups:
        events: list[dict] = []
        next_token: Optional[str] = None
        iteration = 0
        try:
            while iteration < MAX_ITERATIONS:
                iteration += 1
                params = {
                    "logGroupName": group,
                    "startTime": start_ms,
                    "endTime": end_ms,
                    "limit": 200,  # Reduced from 1000 for faster response
                }
                if log_stream:
                    params["logStreamNames"] = [log_stream]
                if next_token:
                    params["nextToken"] = next_token
                
                response = client.filter_log_events(**params)
                batch = response.get("events", [])
                events.extend(batch)
                
                # Early exit if we hit limit
                if len(events) >= MAX_EVENTS_PER_GROUP:
                    logger.warning(f"Hit max events ({MAX_EVENTS_PER_GROUP}) for {group}, truncating")
                    events = events[:MAX_EVENTS_PER_GROUP]
                    break
                
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
    if normalized_level:
        formatted = [log for log in formatted if _level_passes_filter(log.type, normalized_level)]

    formatted.sort(key=lambda e: e.timestamp)
    
    # Final safety cap: limit total logs returned to prevent slow frontend rendering
    MAX_TOTAL_LOGS = 1000
    if len(formatted) > MAX_TOTAL_LOGS:
        logger.warning(f"Total logs ({len(formatted)}) exceeds max ({MAX_TOTAL_LOGS}), truncating")
        formatted = formatted[-MAX_TOTAL_LOGS:]  # Keep most recent
    
    return AdminLogsResponse(status=200, logs=formatted)
