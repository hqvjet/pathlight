"""Client wrapper for Course Service interactions."""
from __future__ import annotations
import logging
from typing import Dict
import requests
from services.token_service import create_access_token
from config import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 1.5

__all__ = ["get_course_stats"]

def _headers(email: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(email)}"}

def get_course_stats(user_email: str) -> dict:
    try:
        base = f"{config.COURSE_SERVICE_URL}/course"
        courses_resp = requests.get(f"{base}/all", headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
        courses_data = courses_resp.json() if courses_resp.status_code == 200 else {"courses": []}
        total_courses = len(courses_data.get("courses", []))
        # Count completed courses from finish flag
        completed_courses = sum(1 for c in courses_data.get("courses", []) if c.get("finish"))
        # Skip per-course lesson enumeration to avoid N+1 latency; approximate from course payload if provided
        total_lessons = sum(c.get("lesson_num", 0) for c in courses_data.get("courses", []))
        return {"total_courses": total_courses, "completed_courses": completed_courses, "total_lessons": total_lessons}
    except Exception as e:  # pragma: no cover
        logger.error(f"Course stats error: {e}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
