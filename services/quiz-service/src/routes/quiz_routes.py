from fastapi import APIRouter, Request, Query
from typing import Optional

from src.controllers.quiz_controller import (
    create_quiz_controller,
    create_manual_quiz_controller,
    get_quiz_detail_controller,
    list_user_quizzes_controller,
    list_public_quizzes_controller,
    submit_quiz_controller,
    update_visibility_controller,
    finish_quiz_controller,
    start_quiz_controller,
    delete_quiz_controller,
    list_all_quizzes_admin_controller,
    delete_quiz_admin_controller,
    toggle_quiz_visibility_admin_controller,
    _verify_token,
)
from src.schemas.quiz_schemas import (
    CreateQuizRequest,
    CreateManualQuizRequest,
    QuizDetailResponse,
    QuizListResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizVisibilityUpdate,
    FinishQuizRequest,
)
from src.services.status_service import fetch_generation_status, fetch_user_quiz_generations

# Prefix is attached in main.py via include_router(prefix="/quiz"), so keep router prefix empty to avoid double /quiz/quiz.
router = APIRouter(prefix="", tags=["Quiz"])


@router.get("/status")
def get_generation_status(quiz_id: str = Query(...)):
    """Get generation status for a quiz from DynamoDB."""
    result = fetch_generation_status(quiz_id)
    if not result:
        return {"status": 404, "message": "Không tìm thấy quiz này, xin vui lòng thử lại"}
    return {"status": 200, "body": result}


@router.get("/generations/my")
def list_my_generations(request: Request):
    """List all quiz generations for the current user."""
    user_id = _verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    rows = fetch_user_quiz_generations(user_id)
    # Return empty list if DynamoDB is unavailable, rather than error
    # This allows frontend to show empty state instead of error
    if rows is None:
        return {"status": 200, "items": []}
    return {"status": 200, "items": rows}


@router.post("/create")
def create_quiz(request: Request, body: CreateQuizRequest):
    return create_quiz_controller(request, body)


@router.post("/create/manual")
def create_manual_quiz(request: Request, body: CreateManualQuizRequest):
    """Create a quiz manually (no AI, no EXP reward)."""
    return create_manual_quiz_controller(request, body)


@router.get("/stats")
def get_user_quiz_stats(request: Request):
    """Get aggregated quiz statistics for current user."""
    from src.controllers.quiz_controller import get_user_quiz_stats_controller
    return get_user_quiz_stats_controller(request)


@router.get("/all", response_model=QuizListResponse)
def list_my_quizzes(request: Request):
    return list_user_quizzes_controller(request)


@router.get("/public", response_model=QuizListResponse)
def list_public_quizzes(search: Optional[str] = Query(default=None), owner_id: Optional[str] = Query(default=None)):
    return list_public_quizzes_controller(search, owner_id)


@router.get("/{quiz_id}", response_model=QuizDetailResponse)
def get_quiz_detail(
    quiz_id: str,
    request: Request,
    include_hints: bool = Query(default=True),
    include_explanations: bool = Query(default=True),
):
    return get_quiz_detail_controller(request, quiz_id, include_hints=include_hints, include_explanations=include_explanations)


@router.post("/{quiz_id}/start")
def start_quiz(quiz_id: str, request: Request):
    """Start a quiz session - validates access and logs activity."""
    return start_quiz_controller(request, quiz_id)


@router.post("/{quiz_id}/submit", response_model=QuizSubmitResponse)
def submit_quiz(quiz_id: str, request: Request, body: QuizSubmitRequest):
    return submit_quiz_controller(request, quiz_id, body)


@router.put("/visibility")
def update_visibility(request: Request, body: QuizVisibilityUpdate):
    return update_visibility_controller(request, body)


@router.put("/finish")
def finish_quiz(request: Request, body: FinishQuizRequest):
    return finish_quiz_controller(request, body)


@router.delete("/{quiz_id}")
def delete_quiz(request: Request, quiz_id: str):
    return delete_quiz_controller(request, quiz_id)


# Admin endpoints
@router.get("/admin/quizzes")
def list_all_quizzes_admin(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
    search: Optional[str] = Query(default=None),
):
    """Admin endpoint to list all quizzes in the system."""
    return list_all_quizzes_admin_controller(request, page, limit, search)


@router.delete("/admin/quizzes/{quiz_id}")
def delete_quiz_admin(quiz_id: str, request: Request):
    """Admin endpoint to delete any quiz."""
    return delete_quiz_admin_controller(quiz_id, request)


@router.put("/admin/quizzes/{quiz_id}/visibility")
def toggle_quiz_visibility_admin(
    quiz_id: str,
    request: Request,
    body: QuizVisibilityUpdate,
):
    """Admin endpoint to change quiz visibility."""
    return toggle_quiz_visibility_admin_controller(quiz_id, request, body)
