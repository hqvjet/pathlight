"""Client wrapper for Course Service interactions."""
from __future__ import annotations
import logging
from typing import Dict, Optional
import requests
from services.token_service import create_access_token
from config import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0

__all__ = ["get_course_stats"]


def _headers(user_id: str, email: Optional[str] = None) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, email=email)}"}


def get_course_stats(user_id: str, user_email: Optional[str] = None) -> dict:
    """
    Fetch course statistics for a user from the Course Service.
    Returns dict with keys: total_courses, completed_courses, total_lessons
    
    If course service is unavailable or returns an error, returns zeros for all stats.
    """
    if not user_id:
        logger.error("[COURSE_CLIENT] ❌ Missing user_id; cannot fetch stats")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
    
    # Log configuration for debugging
    logger.info("="*80)
    logger.info(f"[COURSE_CLIENT] 🚀 Starting course stats fetch")
    logger.info(f"[COURSE_CLIENT] 📝 User ID: {user_id}")
    logger.info(f"[COURSE_CLIENT] 📧 Email: {user_email}")
    logger.info(f"[COURSE_CLIENT] 🌐 COURSE_SERVICE_URL: {config.COURSE_SERVICE_URL}")
    
    try:
        base = f"{config.COURSE_SERVICE_URL}/api/course"
        url = f"{base}/all"
        headers = _headers(user_id, user_email)
        
        logger.info(f"[COURSE_CLIENT] 📍 Request URL: {url}")
        logger.info(f"[COURSE_CLIENT] 🔑 Request Headers: {list(headers.keys())}")
        
        # Make the request
        courses_resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        
        logger.info(f"[COURSE_CLIENT] 📊 Response Status: {courses_resp.status_code}")
        logger.info(f"[COURSE_CLIENT] 📋 Response Headers: {dict(courses_resp.headers)}")
        
        # Handle non-200 responses
        if courses_resp.status_code != 200:
            logger.error(f"[COURSE_CLIENT] ❌ Non-200 response: {courses_resp.status_code}")
            logger.error(f"[COURSE_CLIENT] Response body preview: {courses_resp.text[:500]}")
            return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
        
        # Parse JSON response
        try:
            courses_data = courses_resp.json()
        except ValueError as json_err:
            logger.error(f"[COURSE_CLIENT] ❌ Failed to parse JSON response: {json_err}")
            logger.error(f"[COURSE_CLIENT] Response text: {courses_resp.text[:500]}")
            return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
        
        logger.info(f"[COURSE_CLIENT] 🔍 Response type: {type(courses_data)}")
        if isinstance(courses_data, dict):
            logger.info(f"[COURSE_CLIENT] 🔑 Response keys: {list(courses_data.keys())}")
        
        # Extract courses list
        courses_list = courses_data.get("courses", []) if isinstance(courses_data, dict) else []
        logger.info(f"[COURSE_CLIENT] 📚 Found {len(courses_list)} courses")
        
        if len(courses_list) > 0:
            sample = courses_list[0]
            logger.info(f"[COURSE_CLIENT] 📖 Sample course keys: {list(sample.keys()) if isinstance(sample, dict) else 'N/A'}")
            logger.info(f"[COURSE_CLIENT] 📖 Sample course data: {sample}")
        else:
            logger.warning(f"[COURSE_CLIENT] ⚠️ No courses found for user {user_id}")
        
        # Calculate statistics
        total_courses = len(courses_list)
        completed_courses = sum(1 for c in courses_list if isinstance(c, dict) and c.get("finish"))
        total_lessons = sum(
            c.get("lesson_num", c.get("num_lessons", 0)) 
            for c in courses_list 
            if isinstance(c, dict)
        )
        
        result = {
            "total_courses": total_courses, 
            "completed_courses": completed_courses, 
            "total_lessons": total_lessons
        }
        
        logger.info(f"[COURSE_CLIENT] ✅ Final Stats: {result}")
        logger.info("="*80)
        
        return result
        
    except requests.exceptions.Timeout as e:
        logger.error(f"[COURSE_CLIENT] ⏱️ TIMEOUT ERROR after {DEFAULT_TIMEOUT}s: {e}")
        logger.error(f"[COURSE_CLIENT] Course service may be slow or unreachable at {config.COURSE_SERVICE_URL}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[COURSE_CLIENT] 🔌 CONNECTION ERROR: {e}")
        logger.error(f"[COURSE_CLIENT] Cannot connect to course service at {config.COURSE_SERVICE_URL}")
        logger.error(f"[COURSE_CLIENT] Please verify:")
        logger.error(f"[COURSE_CLIENT]   1. Course service is running")
        logger.error(f"[COURSE_CLIENT]   2. COURSE_SERVICE_URL environment variable is correct")
        logger.error(f"[COURSE_CLIENT]   3. Network connectivity between services")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
        
    except Exception as e:  # pragma: no cover
        logger.error(f"[COURSE_CLIENT] ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"[COURSE_CLIENT] Traceback:\n{traceback.format_exc()}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
