"""Activity tracking service for user milestones (login, lessons, quizzes, etc.)."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Dict, List
from sqlalchemy.orm import Session

from models import LearningActivity, User
from schemas.user_schemas import ActivityLogRequest, ActivityLogResponse, ActivitySeriesResponse, ActivityItem

logger = logging.getLogger(__name__)

# Point mapping per event type
_EVENT_POINTS: Dict[str, int] = {
    "login": 1,
    "complete_lesson": 2,
    "complete_course": 3,
    "complete_quiz": 2,
    "streak": 1,
}


def _normalize_date(dt: datetime | None = None) -> datetime:
    base = dt or datetime.now(timezone.utc)
    return base.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def log_activity(request: ActivityLogRequest, current_user: User, db: Session) -> ActivityLogResponse:
    points = _EVENT_POINTS.get(request.event, 0)
    if points <= 0:
        return ActivityLogResponse(status=400, message="Sự kiện không hợp lệ")

    day = _normalize_date()
    date_key = day.date().isoformat()
    weekday = day.strftime("%A")

    try:
        record = (
            db.query(LearningActivity)
            .filter(LearningActivity.user_id == current_user.id, LearningActivity.date == day)
            .first()
        )
        if not record:
            record = LearningActivity(user_id=current_user.id, date=day, date_of_the_week=weekday, count=points)
            db.add(record)
        else:
            record.count = int(record.count or 0) + points
        db.commit()
        total = int(record.count)
        logger.info("Activity logged: user=%s event=%s points=%s total=%s", current_user.id, request.event, points, total)
        return ActivityLogResponse(status=200, date=date_key, added_points=points, total_points=total)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to log activity for user %s: %s", current_user.id, exc)
        db.rollback()
        return ActivityLogResponse(status=500, message="Không thể lưu hoạt động")


def get_activity_series(current_user: User, db: Session, days: int = 365) -> ActivitySeriesResponse:
    cutoff = _normalize_date().date().toordinal() - days
    try:
        rows: List[LearningActivity] = (
            db.query(LearningActivity)
            .filter(LearningActivity.user_id == current_user.id)
            .all()
        )
        items: List[ActivityItem] = []
        for row in rows:
            if not row.date:
                continue
            ordinal = row.date.date().toordinal()
            if ordinal < cutoff:
                continue
            items.append(ActivityItem(date=row.date.date().isoformat(), points=int(row.count or 0)))
        items.sort(key=lambda x: x.date)
        return ActivitySeriesResponse(status=200, items=items)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch activity series for user %s: %s", current_user.id, exc)
        return ActivitySeriesResponse(status=500, message="Không thể tải hoạt động")
