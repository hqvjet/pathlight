from fastapi import APIRouter, Request
from src.controllers.quiz_controller import (
    get_quizzes_controller,
    create_quiz_controller,
    get_quiz_controller,
    update_quiz_controller,
    delete_quiz_controller
)

router = APIRouter(prefix="/api/v1/quizzes", tags=["Quizzes"])

@router.get("")
def get_quizzes():
    return get_quizzes_controller()

@router.post("")
def create_quiz(request: Request):
    return create_quiz_controller(request)

@router.get("/{quiz_id}")
def get_quiz(quiz_id: int):
    return get_quiz_controller(quiz_id)

@router.put("/{quiz_id}")
def update_quiz(quiz_id: int, request: Request):
    return update_quiz_controller(quiz_id, request)

@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: int, request: Request):
    return delete_quiz_controller(quiz_id, request)
