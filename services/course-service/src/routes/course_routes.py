from fastapi import APIRouter, Request, Depends
from src.controllers.course_controller import (
    get_courses_controller,
    create_course_controller,
    get_course_controller,
    update_course_controller,
    delete_course_controller
)

router = APIRouter(prefix="", tags=["Courses Service"])

@router.get("")
def get_courses():
    return get_courses_controller()

@router.post("")
def create_course(request: Request):
    return create_course_controller(request)

@router.get("/{course_id}")
def get_course(course_id: int):
    return get_course_controller(course_id)

@router.put("/{course_id}")
def update_course(course_id: int, request: Request):
    return update_course_controller(course_id, request)

@router.delete("/{course_id}")
def delete_course(course_id: int, request: Request):
    return delete_course_controller(course_id, request)
