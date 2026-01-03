# pyright: reportArgumentType=false, reportAssignmentType=false, reportCallIssue=false
import logging
import os
from uuid import uuid4
from typing import Optional

import boto3
import httpx
from botocore.exceptions import ClientError
from fastapi import Request, HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from src.config import config
from src.database import get_session
from src.models import Quiz, QuizCard
from src.schemas.quiz_schemas import (
    CreateQuizRequest,
    QuizDetail,
    QuizDetailResponse,
    QuizListResponse,
    QuizSummary,
    QuizCardItem,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizSubmitResult,
    QuizSubmitResultItem,
    QuizVisibilityUpdate,
    FinishQuizRequest,
)
from src.services.sqs_publisher import send_generate_with_vectorize

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".pptx", ".ppt", ".docx", ".doc"}

# Experience rewards
DIFFICULTY_EXP = {
    "easy": 5,
    "medium": 10,
    "hard": 15,
}
QUIZ_COMPLETION_EXP = 50  # Bonus for completing entire quiz


def _get_db() -> Session:
    SessionLocal = get_session()
    return SessionLocal()


def _verify_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    if getattr(config, "JWT_SECRET_KEY", None):
        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            for key in ("sub", "user_id", "uid", "id"):
                if payload.get(key):
                    return str(payload[key])
        except Exception as e:
            logger.warning("JWT verification failed, falling back to unverified claims: %s", e)
    try:
        claims = jwt.get_unverified_claims(token)
        for key in ("sub", "user_id", "uid", "id"):
            if claims.get(key):
                return str(claims[key])
    except Exception as e:
        logger.error("Failed to parse JWT claims: %s", e)
    return None


def _user_service_base_url() -> Optional[str]:
    return os.getenv("USER_SERVICE_URL")


def _award_experience(request: Request, user_id: str, exp_amount: int) -> Optional[dict]:
    """Call user-service to add experience for the current user.
    Returns a dict with status_code and body when the call was attempted, otherwise None.
    """
    if exp_amount <= 0:
        return None
    base_url = _user_service_base_url()
    auth_header = request.headers.get("Authorization")
    if not base_url or not auth_header:
        return None
    url = f"{base_url.rstrip('/')}/user/experience/add"
    try:
        resp = httpx.post(
            url,
            headers={"Authorization": auth_header},
            json={"exp": exp_amount},
            timeout=5.0,
        )
        data = resp.json() if resp.content else {}
        return {"status_code": resp.status_code, "body": data}
    except Exception as e:
        logger.error("Failed to award experience for user %s: %s", user_id, e)
        return None


def _experience_payload(gained_exp: int, award_result: Optional[dict]) -> dict:
    payload = {"gained_exp": gained_exp}
    if award_result and isinstance(award_result.get("body"), dict):
        stats = award_result["body"].get("updated_stats") or {}
        payload.update(  # type: ignore[arg-type]
            {
                "new_level": stats.get("new_level") or stats.get("level"),
                "new_exp": stats.get("new_exp") or stats.get("current_exp"),
                "require_exp": stats.get("new_require_exp") or stats.get("require_exp"),
                "exp_needed_for_next": stats.get("exp_needed_for_next"),
                "rank": stats.get("rank"),
            }
        )
    return payload


def _log_activity(request: Request, user_id: Optional[str], event: str) -> Optional[dict]:
    if not user_id:
        return None
    base_url = _user_service_base_url()
    auth_header = request.headers.get("Authorization")
    if not base_url or not auth_header:
        return None
    url = f"{base_url.rstrip('/')}/user/activity"
    try:
        resp = httpx.post(url, headers={"Authorization": auth_header}, json={"event": event}, timeout=5.0)
        data = resp.json() if resp.content else {}
        return {"status_code": resp.status_code, "body": data}
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("Failed to log activity for user %s: %s", user_id, exc)
        return None


def _ensure_owner_or_public(quiz: Quiz, user_id: Optional[str]):
    is_owner = quiz.user_id == (user_id or "")
    if not is_owner and not quiz.publish:  # type: ignore[arg-type]
        raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào quiz này")
    return is_owner


def _quiz_to_summary(q: Quiz) -> QuizSummary:
    return QuizSummary(  # type: ignore[arg-type]
        quiz_id=q.quiz_id,
        title=q.title,
        overview=q.overview,
        level=q.level,
        duration=q.duration,
        publish=bool(q.publish),
        finish=bool(q.finish),
        num_questions=q.num_questions,
        previous_score=q.previous_score,
        owner_id=q.user_id,
        created_at=q.created_at.isoformat() if q.created_at else "",  # type: ignore[arg-type]
    )


def _admin_guard(request: Request):
    """Verify admin role from JWT token claims."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Admin guard: Missing or invalid Authorization header")
        return {"status": 401, "message": "Unauthorized"}
    
    token = auth_header.split(" ")[1]
    try:
        # Try verified decode first
        payload = None
        secret_key = getattr(config, "JWT_SECRET_KEY", None)
        logger.info(f"Admin guard: JWT_SECRET_KEY configured: {bool(secret_key)}")
        
        if secret_key:
            try:
                payload = jwt.decode(token, secret_key, algorithms=[config.JWT_ALGORITHM])
                logger.info("Admin guard: JWT verified successfully")
            except Exception as e:
                logger.warning(f"Admin guard: JWT verification failed: {e}, trying unverified")
        
        # Fallback to unverified claims
        if not payload:
            try:
                payload = jwt.get_unverified_claims(token)
                logger.info("Admin guard: Using unverified JWT claims")
            except Exception as decode_error:
                logger.error(f"Admin guard: Cannot decode token: {decode_error}")
                return {"status": 401, "message": "Invalid token"}
        
        # Check admin role
        role = payload.get("role")
        roles = payload.get("roles") or []
        if isinstance(roles, str):
            roles = [roles]
        is_admin = role == "admin" or "admin" in roles
        
        logger.info(f"Admin guard: role={role}, roles={roles}, is_admin={is_admin}")
        
        if not is_admin:
            return {"status": 403, "message": "Admin access required"}
        
        logger.info("Admin guard: Access granted")
        return None
    except Exception as e:
        logger.error(f"Admin guard failed: {e}", exc_info=True)
        return {"status": 500, "message": "Cannot verify admin status"}


def create_quiz_controller(request: Request, body: CreateQuizRequest):
    queue_url = os.getenv("SQS_QUEUE_URL")
    if not queue_url:
        raise HTTPException(status_code=500, detail="SQS_QUEUE_URL is not configured")

    short_prompt = (body.short_prompt or body.short_user_prompt or "").strip()
    if not short_prompt or not short_prompt.strip():
        raise HTTPException(status_code=400, detail="short_prompt is required")

    job_type = body.type or "generate_quiz"
    allowed_job_types = {"generate_course", "generate_quiz"}
    if job_type not in allowed_job_types:
        raise HTTPException(status_code=400, detail="type must be one of generate_course, generate_quiz")

    quiz_id = body.quiz_id or f"quiz-{uuid4()}"
    s3_keys = (body.documents or []) + (body.s3_key or [])

    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body.user_id = user_id
    user_prefix = f"users/{user_id}/"
    normalized_s3_keys = []
    for key in s3_keys:
        if not key:
            continue
        normalized_s3_keys.append(key if key.startswith(user_prefix) else user_prefix + key.lstrip('/'))
    s3_keys = normalized_s3_keys

    region = getattr(config, "REGION", None) or os.getenv("REGION") or "ap-northeast-1"
    if s3_keys:
        bucket = getattr(config, "S3_BUCKET_NAME", None) or os.getenv("S3_BUCKET_NAME")
        if not bucket:
            raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured")
        s3 = boto3.client("s3", region_name=region)
        max_bytes = MAX_UPLOAD_BYTES
        try:
            for key in s3_keys:
                head = s3.head_object(Bucket=bucket, Key=key)
                size = int(head.get("ContentLength", 0))
                if size > max_bytes:
                    raise HTTPException(status_code=400, detail=f"File exceeds 25MB: {key}")
        except ClientError as ce:
            code = ce.response.get("Error", {}).get("Code")
            last_key = s3_keys[-1] if s3_keys else "unknown"
            if code in ("404", "NoSuchKey", "NotFound"):
                raise HTTPException(status_code=400, detail=f"S3 key not found: {last_key}")
            raise HTTPException(status_code=500, detail=f"Failed to validate S3 objects: {ce}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to validate S3 objects: {e}")

    try:
        resp = send_generate_with_vectorize(
            queue_url=queue_url,
            course_id=quiz_id,
            s3_keys=s3_keys,
            short_prompt=short_prompt,
            user_role=body.user_role or body.user_position or "",
            course_level=body.course_level,
            course_constraint=body.course_constraint,
            course_duration=body.course_duration,
            user_id=user_id,
            region=region,
            group_id=os.getenv("SQS_GROUP_ID"),
            job_type=job_type,
        )
        _log_activity(request, user_id, "create_quiz")
        return {"status": 202, "message": "submitted", "sqs_message_id": resp.get("MessageId"), "quiz_id": quiz_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit quiz job: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {e}")


def create_manual_quiz_controller(request: Request, body):
    """Create a manual quiz directly (no AI generation, no EXP reward)."""
    from uuid import uuid4
    from src.models import Quiz, QuizCard
    from src.schemas.quiz_schemas import CreateManualQuizRequest
    
    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate input
    try:
        data = CreateManualQuizRequest(**body.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {e}")
    
    if not data.title or not data.overview:
        raise HTTPException(status_code=400, detail="title and overview are required")
    
    if not data.cards or len(data.cards) == 0:
        raise HTTPException(status_code=400, detail="At least one card is required")
    
    session = _get_db()
    try:
        quiz_id = f"quiz-{uuid4()}"
        
        # Create quiz with creation_type='manual' (important for EXP logic)
        quiz = Quiz(
            quiz_id=quiz_id,
            user_id=user_id,
            title=data.title,
            overview=data.overview,
            level=data.level,
            duration=data.duration,
            num_questions=len(data.cards),
            publish=False,
            finish=False,
            creation_type='manual',  # Mark as manual (no EXP)
            previous_score=None,
        )
        session.add(quiz)
        
        # Create cards
        for card_data in data.cards:
            card = QuizCard(
                card_id=f"card-{uuid4()}",
                quiz_id=quiz_id,
                question=card_data.question,
                hint=card_data.hint or "",
                explanation=card_data.explanation or "",
                difficulty=card_data.difficulty,
                option1=card_data.option1,
                option2=card_data.option2,
                option3=card_data.option3,
                option4=card_data.option4,
                answer=card_data.answer,
            )
            session.add(card)
        
        session.commit()
        _log_activity(request, user_id, "create_manual_quiz")
        return {"status": 200, "message": "Quiz created successfully", "quiz_id": quiz_id}
    except Exception as e:
        session.rollback()
        logger.error("Failed to create manual quiz: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to create quiz: {e}")
    finally:
        session.close()


def list_all_quizzes_admin_controller(request: Request, page: int, limit: int, search: Optional[str]):
    guard = _admin_guard(request)
    if guard:
        return guard

    session = _get_db()
    try:
        query = session.query(Quiz)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(Quiz.title.ilike(search_pattern))

        total = query.count()
        offset = (page - 1) * limit
        quizzes = query.order_by(Quiz.created_at.desc()).offset(offset).limit(limit).all()

        quiz_list = [
            {
                "quiz_id": q.quiz_id,
                "user_id": q.user_id,
                "title": q.title,
                "overview": q.overview,
                "level": q.level,
                "duration": q.duration,
                "publish": bool(q.publish),
                "finish": bool(q.finish),
                "num_questions": q.num_questions,
                "creation_type": getattr(q, "creation_type", "ai"),
                "created_at": q.created_at.isoformat() if q.created_at is not None else "",
            }
            for q in quizzes
        ]

        return {"status": 200, "quizzes": quiz_list, "total": total}
    finally:
        session.close()


def delete_quiz_admin_controller(quiz_id: str, request: Request):
    guard = _admin_guard(request)
    if guard:
        return guard

    session = _get_db()
    try:
        quiz = session.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        session.delete(quiz)
        session.commit()
        return {"status": 200, "message": "Đã xóa quiz"}
    finally:
        session.close()


def toggle_quiz_visibility_admin_controller(quiz_id: str, request: Request, body: QuizVisibilityUpdate):
    guard = _admin_guard(request)
    if guard:
        return guard

    session = _get_db()
    try:
        quiz = session.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        quiz.publish = body.publish  # type: ignore[assignment]
        session.commit()
        return {"status": 200, "quiz_id": quiz_id, "publish": bool(body.publish)}
    finally:
        session.close()


def get_quiz_detail_controller(
    request: Request,
    quiz_id: str,
    *,
    include_hints: bool = True,
    include_explanations: bool = True,
) -> QuizDetailResponse:
    user_id = _verify_token(request)
    session = _get_db()
    try:
        quiz: Quiz | None = session.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        _ensure_owner_or_public(quiz, user_id)
        cards = session.query(QuizCard).filter(QuizCard.quiz_id == quiz.quiz_id).order_by(QuizCard.created_at.asc()).all()
        card_models = [
            QuizCardItem(  # type: ignore[arg-type]
                card_id=c.card_id,
                quiz_id=c.quiz_id,
                question=c.question,
				hint=c.hint if include_hints else None,
				explanation=c.explanation if include_explanations else None,
                difficulty=c.difficulty,
                option1=c.option1,
                option2=c.option2,
                option3=c.option3,
                option4=c.option4,
            )
            for c in cards
        ]
        detail = QuizDetail(  # type: ignore[arg-type]
            quiz_id=quiz.quiz_id,
            title=quiz.title,
            overview=quiz.overview,
            level=quiz.level,
            duration=quiz.duration,
            publish=bool(quiz.publish),
            finish=bool(quiz.finish),
            num_questions=quiz.num_questions,
            previous_score=quiz.previous_score,
            owner_id=quiz.user_id,
            created_at=quiz.created_at.isoformat() if quiz.created_at else "",  # type: ignore[arg-type]
            cards=card_models,
        )
        return QuizDetailResponse(status=200, quiz=detail)
    finally:
        session.close()


def get_user_quiz_stats_controller(request: Request) -> dict:
    """Get aggregated quiz statistics for a user - for dashboard."""
    user_id = _verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    
    session = _get_db()
    try:
        # Count total quizzes
        total_quizzes = session.query(Quiz).filter(Quiz.user_id == user_id).count()
        
        # Count completed quizzes (finish=True)
        completed_quizzes = session.query(Quiz).filter(
            Quiz.user_id == user_id,
            Quiz.finish.is_(True)
        ).count()
        
        # Calculate average score from completed quizzes
        completed_quiz_rows = session.query(Quiz.previous_score).filter(
            Quiz.user_id == user_id,
            Quiz.finish.is_(True),
            Quiz.previous_score.isnot(None)
        ).all()
        
        scores = [row.previous_score for row in completed_quiz_rows if row.previous_score is not None]
        average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        
        return {
            "status": 200,
            "total_quizzes": total_quizzes,
            "completed_quizzes": completed_quizzes,
            "average_score": average_score,
        }
    finally:
        session.close()


def list_user_quizzes_controller(request: Request) -> QuizListResponse:
    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = _get_db()
    try:
        rows = session.query(Quiz).filter(Quiz.user_id == user_id).all()
        return QuizListResponse(status=200, quizzes=[_quiz_to_summary(r) for r in rows])
    finally:
        session.close()


def list_public_quizzes_controller(search: Optional[str] = None, owner_id: Optional[str] = None) -> QuizListResponse:
    session = _get_db()
    try:
        query = session.query(Quiz).filter(Quiz.publish.is_(True))
        if owner_id:
            query = query.filter(Quiz.user_id == owner_id)
        if search:
            pattern = f"%{search}%"
            query = query.filter(Quiz.title.ilike(pattern))
        rows = query.all()
        return QuizListResponse(status=200, quizzes=[_quiz_to_summary(r) for r in rows])
    finally:
        session.close()


def submit_quiz_controller(request: Request, quiz_id: str, body: QuizSubmitRequest) -> QuizSubmitResponse:
    user_id = _verify_token(request)
    session = _get_db()
    try:
        quiz = session.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            return QuizSubmitResponse(status=404, message="Không tìm thấy quiz")
        _ensure_owner_or_public(quiz, user_id)
        cards = session.query(QuizCard).filter(QuizCard.quiz_id == quiz.quiz_id).all()
        if not cards:
            return QuizSubmitResponse(status=400, message="Quiz chưa có câu hỏi")
        card_map = {c.card_id: c for c in cards}  # type: ignore[misc]
        if not body.answers or len(body.answers) < len(cards):
            return QuizSubmitResponse(status=400, message="Vui lòng trả lời tất cả câu hỏi")
        correct_count = 0
        results: list[QuizSubmitResultItem] = []
        for ans in body.answers:
            card = card_map.get(ans.card_id)  # type: ignore[arg-type]
            if not card:
                continue
            selected = int(ans.answer)
            correct = int(card.answer)  # type: ignore[arg-type]
            is_correct = selected == correct
            if is_correct:
                correct_count += 1
            results.append(
                QuizSubmitResultItem(  # type: ignore[arg-type]
                    card_id=card.card_id,
                    selected_answer=selected,
                    correct_answer=correct,
                    is_correct=is_correct,
                    difficulty=card.difficulty,
                    explanation=card.explanation,
                )
            )
        total = len(cards)
        score = round((correct_count / total) * 100, 2)
        
        # Calculate experience based on difficulty and performance
        gained_exp = 0
        if score >= 70:  # Only award exp if passed (70% or higher)
            for result in results:
                if result.is_correct:
                    difficulty = result.difficulty.lower() if result.difficulty else "medium"
                    gained_exp += DIFFICULTY_EXP.get(difficulty, DIFFICULTY_EXP["medium"])
        
        # update best score on quiz
        if quiz.previous_score is None or score > quiz.previous_score:  # type: ignore[arg-type]
            quiz.previous_score = int(score)  # type: ignore[assignment]
        session.commit()
        
        # Award experience if quiz passed
        award_result = None
        if gained_exp > 0 and user_id:
            award_result = _award_experience(request, user_id, gained_exp)
        
        _log_activity(request, user_id, "quiz_submit")
        
        experience = _experience_payload(gained_exp, award_result) if gained_exp > 0 else None
        
        return QuizSubmitResponse(
            status=200,
            result=QuizSubmitResult(
                score=score,
                correct_count=correct_count,
                total=total,
                answers=results,
            ),
            experience=experience,
        )
    except Exception as e:
        session.rollback()
        logger.error("submit_quiz_controller error user=%s quiz=%s err=%s", user_id, quiz_id, e)
        return QuizSubmitResponse(status=500, message="Có lỗi xảy ra")
    finally:
        session.close()


def update_visibility_controller(request: Request, body: QuizVisibilityUpdate):
    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = _get_db()
    try:
        quiz = session.query(Quiz).filter(Quiz.quiz_id == body.quiz_id, Quiz.user_id == user_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        quiz.publish = bool(body.publish)  # type: ignore[assignment,misc]
        session.commit()
        return {"status": 200, "quiz_id": quiz.quiz_id, "publish": quiz.publish}
    finally:
        session.close()


def finish_quiz_controller(request: Request, body: FinishQuizRequest):
    """Mark quiz as finished and award completion bonus."""
    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = _get_db()
    try:
        quiz = session.query(Quiz).filter(Quiz.quiz_id == body.quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        
        # Check if user has access (owner or public)
        is_owner = quiz.user_id == user_id
        if not is_owner and not quiz.publish:  # type: ignore[arg-type]
            raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập quiz này")
        
        # Only award exp if not already finished and passed (score >= 70)
        already_finished = bool(quiz.finish)
        if is_owner:  # type: ignore[arg-type]
            quiz.finish = True  # type: ignore[assignment]
        session.commit()
        
        # Award completion bonus if quiz passed and not already finished
        # IMPORTANT: Do NOT award EXP for manual quizzes (to prevent spam)
        exp_amount = 0
        is_manual = getattr(quiz, 'creation_type', 'ai') == 'manual'
        prev_score = quiz.previous_score
        if not already_finished and not is_manual and prev_score is not None and prev_score >= 70:  # type: ignore[arg-type]
            exp_amount = QUIZ_COMPLETION_EXP
        
        award_result = _award_experience(request, user_id, exp_amount) if exp_amount > 0 else None
        experience = _experience_payload(exp_amount, award_result)
        
        _log_activity(request, user_id, "quiz_finish")
        return {"status": 200, "message": "Đã cập nhật thành công", "experience": experience}
    finally:
        session.close()


def start_quiz_controller(request: Request, quiz_id: str):
    """Start a quiz session - validates access and returns quiz ready to play."""
    from datetime import datetime
    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = _get_db()
    try:
        quiz = session.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        _ensure_owner_or_public(quiz, user_id)
        _log_activity(request, user_id, "quiz_start")
        return {
            "status": 200,
            "message": "Bắt đầu quiz thành công",
            "quiz_id": quiz.quiz_id,
            "started_at": datetime.utcnow().isoformat()
        }
    finally:
        session.close()


def delete_quiz_controller(request: Request, quiz_id: str):
    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = _get_db()
    try:
        quiz = session.query(Quiz).filter(Quiz.quiz_id == quiz_id, Quiz.user_id == user_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Không tìm thấy quiz")
        session.delete(quiz)
        session.commit()
        return {"status": 200, "message": "Đã xóa quiz"}
    finally:
        session.close()
