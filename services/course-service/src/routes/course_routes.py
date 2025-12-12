from fastapi import APIRouter, Request, UploadFile, File, Depends, Query
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError
from src.config import config
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
    get_quiz_controller,
    submit_quiz_controller,
    finish_course_controller,
    finish_lesson_controller,
)
from src.services.course_auth import require_bearer
from src.services.status_service import fetch_generation_status, fetch_user_generations
from src.services.sqs_publisher import send_generate_with_vectorize
from src.schemas.course_schemas import (
    CreateCourseRequest,
    CourseFullInfoResponse,
    CourseFullInfo,
    LessonInfo,
    CourseListResponse,
    CourseSummary,
    LessonListResponse,
    LessonDetail,
    AssessmentListResponse,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    QuizResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    FinishCourseRequest,
    FinishLessonRequest,
    PresignUploadRequest,
    PresignUploadResponse,
)
import os
import uuid

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
    """Check generation status for a course by querying DynamoDB.

    Response shape (200):
    {
      "status": 200,
      "body": {
        "status": false,
        "vectorized": true,
        "generated_plan": true,
        "generated_lessons": true,
        "generated_final_test": false
      }
    }
    On not found: {"status": 501, "message": "Không tìm thấy khóa học này, xin vui lòng thử lại"}
    """
    result = fetch_generation_status(course_id)
    if not result:
        return {"status": 501, "message": "Không tìm thấy khóa học này, xin vui lòng thử lại"}
    return {"status": 200, "body": result}


@router.get("/generations/my")
async def list_my_generations(request: Request, _auth=Depends(require_bearer)):
    """List all course generation records in DynamoDB for the current user.

    Response shape (200): { "status": 200, "items": [ { course_id, user_id, progress, ... } ] }
    On error/unauthorized: appropriate status codes with message.
    """
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
    """Create a course by vectorizing S3 documents and running generation in one job.

    Request body (JSON):
      {
        "short_user_prompt": "...",  # required
        "user_position": "Software Engineer",
        "course_duration": 30,
        "course_level": "overview | intermediate | advance",
        "course_constraint": "professional | academic | friendly | humorous",
        "difficulty": "medium",
        "duration": 1200,
        "course_id": "optional-predefined-id",
        "s3_key": ["path/to/file1.pdf"]  # optional
      }

    Constraints:
        - Each referenced S3 file must be <= 15MB
        - Allow prompt-only creation when no s3_key provided
    """
    queue_url = os.getenv("SQS_QUEUE_URL")
    if not queue_url:
        return {"status": 500, "message": "SQS_QUEUE_URL is not configured"}

    # Accept new/legacy prompt fields
    short_prompt = body.short_prompt or body.short_user_prompt
    if not short_prompt or not short_prompt.strip():
        return {"status": 400, "message": "short_prompt is required"}

    # Validate job type (defaults to generate_course)
    job_type = body.type or "generate_course"
    allowed_job_types = {"generate_course", "generate_quiz"}
    if job_type not in allowed_job_types:
        return {"status": 400, "message": "type must be one of generate_course, generate_quiz"}

    course_id = body.course_id or f"course-{uuid.uuid4()}"
    s3_keys = (body.documents or []) + (body.s3_key or [])

    # Normalize user prefix for any provided keys early, before validation
    normalized_s3_keys = []
    from src.controllers.course_controller import _verify_token
    user_id = _verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}
    # body user_id is optional; we trust token and override
    body.user_id = user_id
    user_prefix = f"users/{user_id}/"
    for key in s3_keys:
        if not key:
            continue
        normalized_s3_keys.append(key if key.startswith(user_prefix) else user_prefix + key.lstrip('/'))
    s3_keys = normalized_s3_keys

    # Validate S3 object sizes only when keys are provided
    region = getattr(config, "REGION", None) or os.getenv("REGION") or "ap-northeast-1"
    if s3_keys:
        bucket = getattr(config, "S3_BUCKET_NAME", None) or os.getenv("S3_BUCKET_NAME")
        if not bucket:
            return {"status": 500, "message": "S3_BUCKET_NAME is not configured"}

        s3 = boto3.client("s3", region_name=region)
        max_bytes = 15 * 1024 * 1024  # 15MB
        try:
            for key in s3_keys:
                try:
                    head = s3.head_object(Bucket=bucket, Key=key)
                except ClientError as ce:
                    code = ce.response.get("Error", {}).get("Code")
                    if code in ("404", "NoSuchKey", "NotFound"):
                        return {"status": 400, "message": f"S3 key not found: {key}"}
                    raise
                size = int(head.get("ContentLength", 0))
                if size > max_bytes:
                    return {"status": 400, "message": f"File exceeds 15MB: {key}"}
        except Exception as e:
            return {"status": 500, "message": f"Failed to validate S3 objects: {e}"}

    try:
        resp = send_generate_with_vectorize(
            queue_url=queue_url,
            course_id=course_id,
            s3_keys=s3_keys,
            difficulty=body.difficulty,
            duration=body.duration,
            short_user_prompt=short_prompt,
            user_position=body.user_role or body.user_position,
            course_level=body.course_level,
            course_constraint=body.course_constraint,
            course_duration=body.course_duration,
            user_id=user_id,
            region=region,
            group_id=os.getenv("SQS_GROUP_ID"),
            job_type=job_type,
        )
        return {"status": 202, "message": "submitted", "sqs_message_id": resp.get("MessageId"), "course_id": course_id}
    except Exception as e:
        return {"status": 500, "message": f"Failed to submit job: {e}"}


@router.get("/all", response_model=CourseListResponse)
async def get_all_user_courses(request: Request, _auth=Depends(require_bearer)):
    return get_all_courses_controller(request)


@router.get("/{course_id}", response_model=CourseFullInfoResponse)
async def get_course_full_info(course_id: str, request: Request, _auth=Depends(require_bearer)):
    return get_course_full_info_controller(request, course_id)


@router.get("/{course_id}/lessons", response_model=LessonListResponse)
async def list_course_lessons(course_id: str, request: Request, _auth=Depends(require_bearer)):
    return list_course_lessons_controller(request, course_id)


@router.get("/{course_id}/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson_detail(course_id: str, lesson_id: str, request: Request, _auth=Depends(require_bearer)):
    return get_lesson_detail_controller(request, course_id, lesson_id)


@router.get("/{course_id}/lessons/{lesson_id}/assessments", response_model=AssessmentListResponse)
async def list_assessments(course_id: str, lesson_id: str, request: Request, _auth=Depends(require_bearer)):
    return get_assessment_list_controller(request, course_id, lesson_id)


@router.post("/{course_id}/lessons/{lesson_id}/assessments/submit", response_model=AssessmentSubmitResponse)
async def submit_assessments(course_id: str, lesson_id: str, request: Request, body: AssessmentSubmitRequest, _auth=Depends(require_bearer)):
    return submit_assessment_controller(request, course_id, lesson_id, body)


@router.get("/{course_id}/quiz", response_model=QuizResponse)
async def get_quiz(course_id: str, request: Request, _auth=Depends(require_bearer)):
    return get_quiz_controller(request, course_id)


@router.post("/{course_id}/quiz/submit", response_model=QuizSubmitResponse)
async def submit_quiz(course_id: str, request: Request, body: QuizSubmitRequest, _auth=Depends(require_bearer)):
    return submit_quiz_controller(request, course_id, body)


@router.put("/finish")
async def finish_course(request: Request, body: FinishCourseRequest, _auth=Depends(require_bearer)):
    return finish_course_controller(request, body)


@router.put("/{course_id}/lessons/{lesson_id}/finish")
async def finish_lesson(course_id: str, lesson_id: str, request: Request, _auth=Depends(require_bearer)):
    payload = FinishLessonRequest(course_id=course_id, lesson_id=lesson_id)
    return finish_lesson_controller(request, payload)
