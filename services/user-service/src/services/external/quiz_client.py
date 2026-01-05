"""Client wrapper for Quiz Service interactions."""
from __future__ import annotations
import logging
from typing import Dict, Optional
import requests
from services.token_service import create_access_token
from config import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0

__all__ = ["get_quiz_stats"]


def _headers(user_id: str, email: Optional[str] = None) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, email=email)}"}


def get_quiz_stats(user_id: str, user_email: Optional[str] = None) -> dict:
    if not user_id:
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
    
    try:
        base = f"{config.QUIZ_SERVICE_URL}/api/quiz"
        url = f"{base}/all"
        
        quizzes_resp = requests.get(url, headers=_headers(user_id, user_email), timeout=DEFAULT_TIMEOUT)
        
        if quizzes_resp.status_code != 200:
            return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
        
        quizzes_data = quizzes_resp.json()
        quizzes = quizzes_data.get("quizzes", [])
        
        total_quizzes = len(quizzes)
        
        # Count completed quizzes (those with previous_score set)
        completed_quizzes = [q for q in quizzes if q.get("previous_score") is not None]
        completed = len(completed_quizzes)
        
        # Calculate average score from completed quizzes
        total_score = sum(q.get("previous_score", 0) for q in completed_quizzes)
        average_score = total_score / completed if completed > 0 else 0
        
        return {
            "total_quizzes": total_quizzes,
            "completed_quizzes": completed,
            "average_score": average_score / 100 if average_score > 1 else average_score
        }
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
    except Exception:  # pragma: no cover
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
