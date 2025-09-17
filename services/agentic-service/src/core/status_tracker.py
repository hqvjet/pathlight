"""Generation status tracker backed by DynamoDB.

Schema (DynamoDB Item):
- course_id (PK)
- title_ready: bool
- lessons_ready: bool
- final_ready: bool
- progress: string (free-form)
- updated_at: iso8601

Usage:
- status_tracker.start(course_id)
- status_tracker.mark_plan_ready(course_id, title, desc, roadmap_count)
- status_tracker.mark_lessons_ready(course_id, count)
- status_tracker.mark_final_ready(course_id, count)
"""

from __future__ import annotations

from typing import Optional

from infrastructure.aws.dynamo_client import (
    put_item,
    update_item,
    put_item_strict,
    ensure_table,
    update_item_strict,
)


def start(course_id: str, strict: bool = True) -> None:
    """Initialize or bump progress to 'started' without resetting other flags.

    Uses an upsert/merge so existing fields (e.g., vectorized, plan flags) are preserved.
    """
    updates = {
        "progress": "started",
    }
    if strict:
        ensure_table(strict=True)
        update_item_strict(course_id, updates)
    else:
        update_item(course_id, updates)


def mark_plan_ready(course_id: str, title: Optional[str], description: Optional[str], roadmap_count: int) -> None:
    update_item(
        course_id,
        {
            "title_ready": True,
            "progress": "plan_ready",
            "title": title or "",
            "description": description or "",
            "roadmap_count": roadmap_count,
        },
    )


def mark_lessons_progress(course_id: str, have: int, planned: int) -> None:
    update_item(
        course_id,
        {
            "progress": f"lessons_in_progress {have}/{planned}",
            "lessons_count": have,
            "lessons_planned": planned,
        },
    )


def mark_lessons_ready(course_id: str, count: int) -> None:
    update_item(
        course_id,
        {"lessons_ready": True, "progress": "lessons_ready", "lessons_count": count},
    )


def mark_final_ready(course_id: str, count: int) -> None:
    update_item(
        course_id,
        {"final_ready": True, "progress": "final_ready", "final_count": count},
    )


def mark_vectorized(course_id: str, ok: bool = True) -> None:
    update_item_strict(course_id, {"vectorized": bool(ok)})
