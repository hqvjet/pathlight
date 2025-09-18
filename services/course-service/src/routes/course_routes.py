from fastapi import APIRouter, Request, UploadFile, File, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
import boto3
from botocore.exceptions import ClientError
from src.config import config
from src.controllers.course_controller import (
    upload_files_docs,
    delete_single_course,
    delete_all_courses,
    get_course_full_info_controller,
    get_all_courses_controller,
    list_course_lessons_controller,
    get_lesson_detail_controller,
    get_lesson_test_controller,
    get_final_test_controller,
)
from src.services.course_auth import require_bearer
from src.services.status_service import fetch_generation_status
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
    LessonTestResponse,
    LessonTest,
    LessonTestQA,
    FinalTestResponse,
    FinalTestDetail,
    FinalTestQA,
)
import os

router = APIRouter(prefix="", tags=["Course"])


@router.post("/upload/file")
async def upload_files(request: Request, files: List[UploadFile] = File(...), _auth=Depends(require_bearer)):
    return await upload_files_docs(request, files)

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


@router.post("/create")
async def request_create_course(
    body: CreateCourseRequest,
    request: Request,
    _auth=Depends(require_bearer),
):
    """Create a course by vectorizing S3 documents and running generation in one job.

        Request body (JSON):
      {
        "course_id": "course-123",
        "s3_key": ["path/to/file1.pdf", "path/to/file2.docx"],
        "difficulty": "medium",
        "duration": 1200
      }

    Constraints:
            - s3_key must not be empty
            - Each file must be <= 15MB
    """
    queue_url = os.getenv("SQS_QUEUE_URL")
    if not queue_url:
        return {"status": 500, "message": "SQS_QUEUE_URL is not configured"}

    if not body.s3_key:
        return {"status": 400, "message": "s3_key must contain at least one key"}

    # Validate S3 object sizes
    region = getattr(config, "REGION", None) or os.getenv("REGION") or "ap-northeast-1"
    bucket = getattr(config, "S3_BUCKET_NAME", None) or os.getenv("S3_BUCKET_NAME")
    if not bucket:
        return {"status": 500, "message": "S3_BUCKET_NAME is not configured"}

    s3 = boto3.client("s3", region_name=region)
    max_bytes = 15 * 1024 * 1024  # 15MB
    try:
        for key in body.s3_key:
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

    from src.controllers.course_controller import _verify_token
    user_id = _verify_token(request)
    if not user_id:
        return {"status": 401, "message": "Unauthorized"}

    try:
        resp = send_generate_with_vectorize(
            queue_url=queue_url,
            course_id=body.course_id,
            s3_keys=body.s3_key,
            difficulty=body.difficulty,
            duration=body.duration,
            user_id=user_id,
            region=region,
            group_id=os.getenv("SQS_GROUP_ID"),
        )
        return {"status": 202, "message": "submitted", "sqs_message_id": resp.get("MessageId")}
    except Exception as e:
        return {"status": 500, "message": f"Failed to submit job: {e}"}


@router.get("/all", response_model=CourseListResponse)
async def get_all_user_courses(request: Request, _auth=Depends(require_bearer)):
    # Important: define static route before dynamic '/{course_id}' to prevent route shadowing
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


@router.get("/{course_id}/lessons/{lesson_id}/test", response_model=LessonTestResponse)
async def get_lesson_test(course_id: str, lesson_id: str, request: Request, _auth=Depends(require_bearer)):
    return get_lesson_test_controller(request, course_id, lesson_id)


@router.get("/{course_id}/final-test", response_model=FinalTestResponse)
async def get_final_test(course_id: str, request: Request, _auth=Depends(require_bearer)):
    return get_final_test_controller(request, course_id)
