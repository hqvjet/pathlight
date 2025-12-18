from fastapi import APIRouter, Request, Query
from typing import Optional

from src.controllers.quiz_controller import (
    create_quiz_controller,
    get_quiz_detail_controller,
    list_user_quizzes_controller,
    list_public_quizzes_controller,
    submit_quiz_controller,
    update_visibility_controller,
    finish_quiz_controller,
    delete_quiz_controller,
)
from src.schemas.quiz_schemas import (
    CreateQuizRequest,
    QuizDetailResponse,
    QuizListResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizVisibilityUpdate,
    FinishQuizRequest,
)

router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.post("/create")
def create_quiz(request: Request, body: CreateQuizRequest):
    return create_quiz_controller(request, body)


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
