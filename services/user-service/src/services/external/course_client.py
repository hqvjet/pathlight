"""Client wrapper for Course Service interactions."""
from __future__ import annotations
import logging
from typing import Dict
import requests
from services.token_service import create_access_token
from config import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0

__all__ = ["get_course_stats"]

def _headers(email: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(email)}"}

def get_course_stats(user_email: str) -> dict:
    try:
        base = f"{config.COURSE_SERVICE_URL}/api/course"
        url = f"{base}/all"
        logger.info(f"Fetching course stats from {url} for user {user_email}")
        courses_resp = requests.get(url, headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
        logger.info(f"Course stats response: status={courses_resp.status_code}")
        courses_data = courses_resp.json() if courses_resp.status_code == 200 else {"courses": []}
        total_courses = len(courses_data.get("courses", []))
        completed_courses = sum(1 for c in courses_data.get("courses", []) if c.get("finish"))
        # Sum num_lessons from each course
        total_lessons = sum(c.get("num_lessons", 0) for c in courses_data.get("courses", []))
        logger.info(f"Course stats: total={total_courses}, completed={completed_courses}, lessons={total_lessons}")
        return {"total_courses": total_courses, "completed_courses": completed_courses, "total_lessons": total_lessons}
    except Exception as e:  # pragma: no cover
        logger.error(f"Course stats error: {e}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
