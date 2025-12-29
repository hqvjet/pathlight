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
        logger.info(f"[COURSE_CLIENT] Fetching course stats from {url} for user {user_email}")
        logger.info(f"[COURSE_CLIENT] COURSE_SERVICE_URL = {config.COURSE_SERVICE_URL}")
        
        courses_resp = requests.get(url, headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
        logger.info(f"[COURSE_CLIENT] Response status: {courses_resp.status_code}")
        logger.info(f"[COURSE_CLIENT] Response headers: {dict(courses_resp.headers)}")
        
        if courses_resp.status_code != 200:
            logger.error(f"[COURSE_CLIENT] Non-200 response: {courses_resp.status_code}")
            logger.error(f"[COURSE_CLIENT] Response body: {courses_resp.text[:500]}")
            return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
        
        courses_data = courses_resp.json()
        logger.info(f"[COURSE_CLIENT] Response data keys: {list(courses_data.keys()) if isinstance(courses_data, dict) else 'not a dict'}")
        logger.info(f"[COURSE_CLIENT] Full response: {courses_data}")
        
        courses_list = courses_data.get("courses", [])
        logger.info(f"[COURSE_CLIENT] Found {len(courses_list)} courses in response")
        
        if len(courses_list) > 0:
            logger.info(f"[COURSE_CLIENT] Sample course: {courses_list[0]}")
        
        total_courses = len(courses_list)
        completed_courses = sum(1 for c in courses_list if c.get("finish"))
        total_lessons = sum(c.get("num_lessons", 0) for c in courses_list)
        
        logger.info(f"[COURSE_CLIENT] ✅ Stats: total={total_courses}, completed={completed_courses}, lessons={total_lessons}")
        return {"total_courses": total_courses, "completed_courses": completed_courses, "total_lessons": total_lessons}
    except requests.exceptions.Timeout as e:
        logger.error(f"[COURSE_CLIENT] ⏱️ Timeout error: {e}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[COURSE_CLIENT] 🔌 Connection error: {e}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
    except Exception as e:  # pragma: no cover
        logger.error(f"[COURSE_CLIENT] ❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"[COURSE_CLIENT] Traceback: {traceback.format_exc()}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
