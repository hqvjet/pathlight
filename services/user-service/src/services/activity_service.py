"""Activity tracking service for learning actions."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from datetime import timedelta
from typing import Dict, List
from sqlalchemy.orm import Session

from models import LearningActivity, User
from schemas.user_schemas import ActivityLogRequest, ActivityLogResponse, ActivitySeriesResponse, ActivityItem
from services.experience_service import auto_level_up

logger = logging.getLogger(__name__)

_EVENT_POINTS: Dict[str, int] = {
    "course_move": 3, 
    "quiz_move": 3, 
    "create_course": 1, 
    "create_quiz": 1,     
    "assessment_move": 3,
}


def _normalize_date(dt: datetime | None = None) -> datetime:
    base = dt or datetime.now(timezone.utc)
    return base.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _get_yesterday_activity(user_id: str, day: datetime, db: Session) -> LearningActivity | None:
    prev_day = day - timedelta(days=1)
    return (
        db.query(LearningActivity)
        .filter(LearningActivity.user_id == user_id, LearningActivity.date == prev_day)
        .first()
    )


def log_activity(request: ActivityLogRequest, current_user: User, db: Session) -> ActivityLogResponse:
    points = _EVENT_POINTS.get(request.event, 0)
    if points <= 0:
        return ActivityLogResponse(status=400, message=f"Sự kiện không hợp lệ. Hợp lệ: {', '.join(_EVENT_POINTS.keys())}")

    day = _normalize_date()
    date_key = day.date().isoformat()

    try:
        record = (
            db.query(LearningActivity)
            .filter(LearningActivity.user_id == current_user.id, LearningActivity.date == day)
            .first()
        )
        if not record:
            record = LearningActivity(user_id=current_user.id, date=day, count=points)
            db.add(record)
            total = points
        else:
            record.count = int(record.count or 0) + points
            total = int(record.count)

        prev_activity = _get_yesterday_activity(current_user.id, day, db)
        current_streak = int(getattr(current_user, "streak", 0) or 0)
        new_streak = current_streak + 1 if prev_activity else 1
        current_exp = int(getattr(current_user, "current_exp", 0) or 0)
        raw_multiplier = 0.01 * (new_streak + 1)
        bonus_multiplier = min(raw_multiplier, 1.0)  # max +100%
        bonus_exp = int(current_exp * bonus_multiplier)
        new_exp_total = current_exp + bonus_exp
        new_level, next_require_exp, _ = auto_level_up(new_exp_total, getattr(current_user, "level", 1))
        current_user.current_exp = new_exp_total
        current_user.level = new_level
        current_user.require_exp = next_require_exp

        current_user.streak = new_streak

        db.commit()
        logger.info(
            "Activity logged: user=%s event=%s points=%s total=%s streak=%s bonus_exp=%s exp=%s level=%s",
            current_user.id,
            request.event,
            points,
            total,
            new_streak,
            bonus_exp,
            new_exp_total,
            new_level,
        )
        return ActivityLogResponse(
            status=200,
            date=date_key,
            added_points=points,
            total_points=total,
            streak=new_streak,
            bonus_exp=bonus_exp if bonus_exp > 0 else None,
            new_exp=new_exp_total,
            new_level=new_level,
            require_exp=next_require_exp,
        )
    except Exception as exc:
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
    except Exception as exc:
        logger.error("Failed to fetch activity series for user %s: %s", current_user.id, exc)
        return ActivitySeriesResponse(status=500, message="Không thể tải hoạt động")
