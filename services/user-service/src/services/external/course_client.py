"""Client wrapper for Course Service interactions."""
from __future__ import annotations
import logging
from typing import Dict
import requests
from services.token_service import create_access_token
from config import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5

__all__ = ["get_course_stats"]

def _headers(email: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(email)}"}

def get_course_stats(user_email: str) -> dict:
    try:
        base = f"{config.COURSE_SERVICE_URL}/api/v1"
        courses_resp = requests.get(f"{base}/courses", headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
        courses_data = courses_resp.json() if courses_resp.status_code == 200 else {"courses": []}
        total_courses = len(courses_data.get("courses", []))
        results_resp = requests.get(f"{base}/user/test-results", headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
        results_data = results_resp.json() if results_resp.status_code == 200 else {"results": []}
        completed_courses = len({r.get("test_id") for r in results_data.get("results", []) if r.get("test_id")})
        total_lessons = 0
        for course in courses_data.get("courses", []):
            cid = course.get("id")
            if not cid:
                continue
            lessons_resp = requests.get(f"{base}/courses/{cid}/lessons", headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
            lessons_data = lessons_resp.json() if lessons_resp.status_code == 200 else {"lessons": []}
            total_lessons += len(lessons_data.get("lessons", []))
        return {"total_courses": total_courses, "completed_courses": completed_courses, "total_lessons": total_lessons}
    except Exception as e:  # pragma: no cover
        logger.error(f"Course stats error: {e}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
