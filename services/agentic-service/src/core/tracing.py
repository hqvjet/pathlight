"""
Lightweight step tracer to make agent logs readable even with large payloads.

Writes single-line JSON logs to a file and also emits compact structured logs
via the application's logger. Designed to be safe in noisy environments.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _ensure_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _preview(value: Any, limit: int = 400) -> Any:
    """Return a compact preview for large values to keep logs readable."""
    try:
        if value is None:
            return None
        if isinstance(value, (int, float, bool)):
            return value
        if isinstance(value, str):
            return value if len(value) <= limit else value[:limit] + "…"  # type: ignore[str-bytes-safe]
        if isinstance(value, (list, tuple)):
            # Show length and first item preview
            return {
                "type": type(value).__name__,
                "len": len(value),
                "head": _preview(value[0], max(50, limit // 4)) if value else None,
            }
        if isinstance(value, dict):
            # Keep only first few keys
            items = list(value.items())[:5]
            return {k: _preview(v, max(50, limit // 4)) for k, v in items}
        # Fallback to string preview
        s = str(value)
        return s if len(s) <= limit else s[:limit] + "…"
    except Exception:
        return "<unpreviewable>"


class StepTracer:
    def __init__(
        self,
        agent_name: str,
        course_id: str,
        *,
        enabled: Optional[bool] = None,
        log_file: Optional[str] = None,
        logger=None,
    ) -> None:
        self.agent = agent_name
        self.course_id = course_id
        self.step = 0
        self.logger = logger
        self.enabled = enabled if enabled is not None else os.environ.get("TRACE_ENABLED", "1") == "1"

        # Choose a Lambda-safe default path: /tmp is writable in Lambda
        is_lambda = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
        if is_lambda:
            default_base = Path(os.environ.get("TRACE_DIR", "/tmp"))
        else:
            default_base = Path(os.environ.get("TRACE_DIR")) if os.environ.get("TRACE_DIR") else Path(os.getcwd()) / "logs"

        default_file = os.environ.get("TRACE_FILE") or str(default_base / "agent_steps.log")
        self.log_file = log_file or default_file
        if self.enabled:
            try:
                _ensure_dir(self.log_file)
            except Exception:
                # If we cannot create directory (e.g. read-only fs), disable file logging
                self.log_file = None

    def record(self, phase: str, summary: str, **kwargs: Any) -> None:
        if not self.enabled:
            return
        self.step += 1
        event: Dict[str, Any] = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "agent": self.agent,
            "course_id": self.course_id,
            "step": self.step,
            "phase": phase,
            "summary": summary,
        }
        if kwargs:
            event["data"] = {k: _preview(v) for k, v in kwargs.items()}

        # Write as JSONL for easy tailing/grep
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
            except Exception:
                # best-effort; if file write fails (e.g. RO fs), stop using file to avoid repeated errors
                self.log_file = None

        # Also emit compact structured line to logger if provided
        if self.logger is not None:
            try:
                from core.logging import log_structured

                log_structured(
                    self.logger,
                    "info",
                    f"[{self.agent}] step={self.step} phase={phase}",
                    course_id=self.course_id,
                    summary=summary,
                )
            except Exception:
                pass
