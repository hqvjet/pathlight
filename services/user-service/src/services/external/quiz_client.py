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
        logger.error("[QUIZ_CLIENT] Missing user_id; cannot fetch stats")
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
    try:
        base = f"{config.QUIZ_SERVICE_URL}/api/quiz"
        url = f"{base}/all"
        logger.info(f"[QUIZ_CLIENT] Fetching quiz stats from {url} for user_id={user_id} email={user_email}")
        logger.info(f"[QUIZ_CLIENT] QUIZ_SERVICE_URL = {config.QUIZ_SERVICE_URL}")
        
        quizzes_resp = requests.get(url, headers=_headers(user_id, user_email), timeout=DEFAULT_TIMEOUT)
        logger.info(f"[QUIZ_CLIENT] Response status: {quizzes_resp.status_code}")
        logger.info(f"[QUIZ_CLIENT] Response headers: {dict(quizzes_resp.headers)}")
        
        if quizzes_resp.status_code != 200:
            logger.error(f"[QUIZ_CLIENT] Non-200 response: {quizzes_resp.status_code}")
            logger.error(f"[QUIZ_CLIENT] Response body: {quizzes_resp.text[:500]}")
            return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
        
        quizzes_data = quizzes_resp.json()
        logger.info(f"[QUIZ_CLIENT] Response data keys: {list(quizzes_data.keys()) if isinstance(quizzes_data, dict) else 'not a dict'}")
        logger.info(f"[QUIZ_CLIENT] Full response: {quizzes_data}")
        
        quizzes = quizzes_data.get("quizzes", [])
        logger.info(f"[QUIZ_CLIENT] Found {len(quizzes)} quizzes in response")
        
        total_quizzes = len(quizzes)
        
        # Count completed quizzes (those with previous_score set)
        completed_quizzes = [q for q in quizzes if q.get("previous_score") is not None]
        completed = len(completed_quizzes)
        
        # Calculate average score from completed quizzes
        total_score = sum(q.get("previous_score", 0) for q in completed_quizzes)
        average_score = total_score / completed if completed > 0 else 0
        
        logger.info(f"[QUIZ_CLIENT] ✅ Stats: total={total_quizzes}, completed={completed}, avg_score={average_score}")
        return {
            "total_quizzes": total_quizzes,
            "completed_quizzes": completed,
            "average_score": average_score / 100 if average_score > 1 else average_score
        }
    except requests.exceptions.Timeout as e:
        logger.error(f"[QUIZ_CLIENT] ⏱️ Timeout error: {e}")
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[QUIZ_CLIENT] 🔌 Connection error: {e}")
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
    except Exception as e:  # pragma: no cover
        logger.error(f"[QUIZ_CLIENT] ❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"[QUIZ_CLIENT] Traceback: {traceback.format_exc()}")
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}
