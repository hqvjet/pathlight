from fastapi import APIRouter, Request, UploadFile, File, Depends, Query
from typing import List, Optional
from src.controllers.course_controller import upload_files_docs, delete_single_course, delete_all_courses
from src.services.course_auth import require_bearer
from src.services.status_service import fetch_generation_status
from src.services.sqs_publisher import send_generate_with_vectorize
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


@router.post("/generate")
async def request_generate_course(
    request: Request,
    course_id: str,
    s3_keys: List[str] = Query(...),
    difficulty: str = Query("medium"),
    duration: int = Query(1200),
    _auth=Depends(require_bearer),
):
    """Submit a single job that vectorizes provided S3 files and generates the course.

    Expects Query params:
      - course_id: str
      - s3_keys: repeated query params (?s3_keys=path1&s3_keys=path2)
      - difficulty: default medium
      - duration: default 1200

    Returns 202 with basic submission info.
    """
    queue_url = os.getenv("SQS_QUEUE_URL")
    if not queue_url:
        return {"status": 500, "message": "SQS_QUEUE_URL is not configured"}
    try:
        resp = send_generate_with_vectorize(
            queue_url=queue_url,
            course_id=course_id,
            s3_keys=s3_keys,
            difficulty=difficulty,
            duration=duration,
            region=os.getenv("REGION"),
            group_id=os.getenv("SQS_GROUP_ID"),
        )
        return {"status": 202, "message": "submitted", "sqs_message_id": resp.get("MessageId")}
    except Exception as e:
        return {"status": 500, "message": f"Failed to submit job: {e}"}
