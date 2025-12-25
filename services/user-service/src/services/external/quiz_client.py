"""Client wrapper for Quiz Service interactions."""
from __future__ import annotations
import logging
from typing import Dict
import requests
from services.token_service import create_access_token
from config import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 1.5

__all__ = ["get_quiz_stats"]

def _headers(email: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(email)}"}

def get_quiz_stats(user_email: str) -> dict:
    try:
        base = f"{config.QUIZ_SERVICE_URL}/api/v1"
        quizzes_resp = requests.get(f"{base}/quizzes", headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
        quizzes_data = quizzes_resp.json() if quizzes_resp.status_code == 200 else {"quizzes": []}
        total_quizzes = len(quizzes_data.get("quizzes", []))
        attempts_resp = requests.get(f"{base}/user/quiz-attempts", headers=_headers(user_email), timeout=DEFAULT_TIMEOUT)
        attempts_data = attempts_resp.json() if attempts_resp.status_code == 200 else {"attempts": []}
        attempts = attempts_data.get("attempts", [])
        completed = len(attempts)
        total_score = sum(a.get("score", 0) for a in attempts)
        average_score = total_score / len(attempts) if attempts else 0
        return {
            "total_quizzes": total_quizzes,
            "completed_quizzes": completed,
            "average_score": average_score / 100 if average_score > 1 else average_score
        }
    except Exception as e:  # pragma: no cover
        logger.error(f"Quiz stats error: {e}")
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
