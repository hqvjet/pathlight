"""Client wrapper for Course Service interactions."""
from __future__ import annotations
import logging
from typing import Dict, Optional
import requests
from services.token_service import create_access_token
from config import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0

__all__ = ["get_course_stats", "delete_user_courses"]


def _headers(user_id: str, email: Optional[str] = None) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, email=email)}"}


def get_course_stats(user_id: str, user_email: Optional[str] = None) -> dict:
    """
    Fetch course statistics for a user from the Course Service.
    Returns dict with keys: total_courses, completed_courses, total_lessons
    
    If course service is unavailable or returns an error, returns zeros for all stats.
    """
    if not user_id:
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
    
    try:
        base = f"{config.COURSE_SERVICE_URL}/api/course"
        url = f"{base}/all"
        headers = _headers(user_id, user_email)
        
        courses_resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        
        if courses_resp.status_code != 200:
            return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
        
        try:
            courses_data = courses_resp.json()
        except ValueError:
            return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
        
        courses_list = courses_data.get("courses", []) if isinstance(courses_data, dict) else []
        
        total_courses = len(courses_list)
        completed_courses = sum(1 for c in courses_list if isinstance(c, dict) and c.get("finish"))
        total_lessons = sum(
            c.get("lesson_num", c.get("num_lessons", 0)) 
            for c in courses_list 
            if isinstance(c, dict)
        )
        
        return {
            "total_courses": total_courses, 
            "completed_courses": completed_courses, 
            "total_lessons": total_lessons
        }
        
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}
        
    except Exception:  # pragma: no cover
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}


def delete_user_courses(user_id: str, admin_email: str) -> bool:
    """
    Delete all courses owned by a specific user (admin operation).
    
    Args:
        user_id: The ID of the user whose courses should be deleted
        admin_email: Email of the admin performing the deletion (for audit logging)
    
    Returns:
        True if deletion was successful, False otherwise
    """
    if not user_id:
        return False
    
    try:
        base = f"{config.COURSE_SERVICE_URL}/api/course"
        url = f"{base}/admin/courses/user/{user_id}"
        headers = _headers(user_id="admin", email=admin_email)
        
        response = requests.delete(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        
        if response.status_code == 200:
            return True
        else:
            return False
            
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        return False
        
    except Exception:  # pragma: no cover
        return False
