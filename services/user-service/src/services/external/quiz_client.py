"""Client wrapper for Quiz Service interactions."""
from __future__ import annotations
import logging
from typing import Dict
import requests
from services.token_service import create_access_token
from config import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0

__all__ = ["get_quiz_stats"]

def _headers(email: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(email)}"}

def get_quiz_stats(user_email: str) -> dict:
    try:
        base = f"{config.QUIZ_SERVICE_URL}/api/quiz"
        url = f"{base}/all"
        logger.info(f"Fetching quiz stats from {url} for user {user_email}")
        quizzes_resp = requests.get(url, headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
        logger.info(f"Quiz stats response: status={quizzes_resp.status_code}")
        quizzes_data = quizzes_resp.json() if quizzes_resp.status_code == 200 else {"quizzes": []}
        quizzes = quizzes_data.get("quizzes", [])
        total_quizzes = len(quizzes)
        
        # Count completed quizzes (those with previous_score set)
        completed_quizzes = [q for q in quizzes if q.get("previous_score") is not None]
        completed = len(completed_quizzes)
        
        # Calculate average score from completed quizzes
        total_score = sum(q.get("previous_score", 0) for q in completed_quizzes)
        average_score = total_score / completed if completed > 0 else 0
        
        logger.info(f"Quiz stats: total={total_quizzes}, completed={completed}, avg_score={average_score}")
        return {
            "total_quizzes": total_quizzes,
            "completed_quizzes": completed,
            "average_score": average_score / 100 if average_score > 1 else average_score
        }
    except Exception as e:  # pragma: no cover
        logger.error(f"Quiz stats error: {e}")
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
