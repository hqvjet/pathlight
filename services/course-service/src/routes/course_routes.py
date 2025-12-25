from fastapi import APIRouter, Request, UploadFile, File, Depends, Query
from typing import List, Optional
from src.controllers.course_controller import (
    upload_files_docs,
    presign_upload_urls,
    delete_single_course,
    delete_all_courses,
    get_course_full_info_controller,
    get_all_courses_controller,
    list_course_lessons_controller,
    get_lesson_detail_controller,
    get_assessment_list_controller,
    submit_assessment_controller,
    finish_course_controller,
    finish_lesson_controller,
    update_course_visibility_controller,
    list_public_courses_controller,
    create_course_controller,
    list_all_courses_admin_controller,
    delete_course_admin_controller,
    toggle_course_visibility_admin_controller,
)
from src.services.course_auth import require_bearer
from src.services.status_service import fetch_generation_status, fetch_user_generations
from src.schemas.course_schemas import (
    CreateCourseRequest,
    CourseFullInfoResponse,
    CourseListResponse,
    LessonListResponse,
    LessonDetail,
    AssessmentListResponse,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    FinishCourseRequest,
    FinishLessonRequest,
    PresignUploadRequest,
    PresignUploadResponse,
    CourseVisibilityUpdate,
)

router = APIRouter(prefix="", tags=["Course"])


@router.post("/upload/file")
async def upload_files(request: Request, files: List[UploadFile] = File(...), _auth=Depends(require_bearer)):
    return await upload_files_docs(request, files)


@router.post("/upload/presign", response_model=PresignUploadResponse)
async def presign_upload(request: Request, body: PresignUploadRequest, _auth=Depends(require_bearer)):
    return await presign_upload_urls(request, body)

@router.delete("/delete")
async def delete_course(request: Request, course_id: Optional[str] = Query(default=None), _auth=Depends(require_bearer)):
    return await delete_single_course(request, course_id)


@router.delete("/delete/all")
async def delete_all_course(request: Request, _auth=Depends(require_bearer)):
    return await delete_all_courses(request)

@router.get("/status")
async def get_generation_status(course_id: str = Query(...), _auth=Depends(require_bearer)):
    result = fetch_generation_status(course_id)
    if not result:
        return {"status": 501, "message": "Không tìm thấy khóa học này, xin vui lòng thử lại"}
    return {"status": 200, "body": result}


@router.get("/generations/my")
async def list_my_generations(request: Request, _auth=Depends(require_bearer)):
    from src.controllers.course_controller import _verify_token
    user_id = _verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    rows = fetch_user_generations(user_id)
    if rows is None:
        return {"status": 500, "message": "Không thể lấy dữ liệu tiến trình"}
    return {"status": 200, "items": rows}


@router.post("/create")
async def request_create_course(
    body: CreateCourseRequest,
    request: Request,
    _auth=Depends(require_bearer),
):
    return await create_course_controller(request, body)


@router.get("/all", response_model=CourseListResponse)
async def get_all_user_courses(request: Request, _auth=Depends(require_bearer)):
    return get_all_courses_controller(request)


@router.get("/public", response_model=CourseListResponse)
async def list_public_courses(search: Optional[str] = Query(default=None), user_id: Optional[str] = Query(default=None)):
    return list_public_courses_controller(search, user_id)


@router.get("/{course_id}", response_model=CourseFullInfoResponse)
async def get_course_full_info(course_id: str, request: Request):
    return get_course_full_info_controller(request, course_id)


@router.get("/{course_id}/lessons", response_model=LessonListResponse)
async def list_course_lessons(course_id: str, request: Request):
    return list_course_lessons_controller(request, course_id)


@router.get("/{course_id}/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson_detail(course_id: str, lesson_id: str, request: Request):
    return get_lesson_detail_controller(request, course_id, lesson_id)


@router.get("/{course_id}/lessons/{lesson_id}/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    course_id: str,
    lesson_id: str,
    request: Request,
    include_hints: bool = Query(default=True),
    include_explanations: bool = Query(default=True),
    _auth=Depends(require_bearer),
):
    return get_assessment_list_controller(request, course_id, lesson_id, include_hints=include_hints, include_explanations=include_explanations)


@router.post("/{course_id}/lessons/{lesson_id}/assessments/submit", response_model=AssessmentSubmitResponse)
async def submit_assessments(course_id: str, lesson_id: str, request: Request, body: AssessmentSubmitRequest, _auth=Depends(require_bearer)):
    return submit_assessment_controller(request, course_id, lesson_id, body)


@router.put("/finish")
async def finish_course(request: Request, body: FinishCourseRequest, _auth=Depends(require_bearer)):
    return finish_course_controller(request, body)


@router.put("/{course_id}/lessons/{lesson_id}/finish")
async def finish_lesson(course_id: str, lesson_id: str, request: Request, _auth=Depends(require_bearer)):
    payload = FinishLessonRequest(course_id=course_id, lesson_id=lesson_id)
    return finish_lesson_controller(request, payload)


@router.put("/visibility")
async def update_visibility(request: Request, body: CourseVisibilityUpdate, _auth=Depends(require_bearer)):
    return update_course_visibility_controller(request, body)


# Admin endpoints
@router.get("/admin/courses")
async def list_all_courses_admin(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=1000),
    search: Optional[str] = Query(default=None),
    _auth=Depends(require_bearer)
):
    return list_all_courses_admin_controller(request, page, limit, search)


@router.delete("/admin/courses/{course_id}")
async def delete_course_admin(course_id: str, request: Request, _auth=Depends(require_bearer)):
    """Admin endpoint to delete any course."""
    return await delete_course_admin_controller(course_id, request)


@router.put("/admin/courses/{course_id}/visibility")
async def toggle_course_visibility_admin(
    course_id: str, 
    request: Request, 
    body: CourseVisibilityUpdate, 
    _auth=Depends(require_bearer)
):
    """Admin endpoint to change course visibility."""
    return await toggle_course_visibility_admin_controller(course_id, request, body)
