from fastapi import APIRouter, Request, UploadFile, File, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
import boto3
from botocore.exceptions import ClientError
from src.config import config
from src.controllers.course_controller import upload_files_docs, delete_single_course, delete_all_courses
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
    user_id = _verify_token(request) or "anonymous"

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


@router.get("/{course_id}", response_model=CourseFullInfoResponse)
async def get_course_full_info(course_id: str, request: Request, _auth=Depends(require_bearer)):
    """Return full information for a single course.

    Uses response_model for 200 only; on unauthorized/not found raises HTTPException to avoid
    FastAPI response validation errors when schema mismatch occurs.
    """
    from src.controllers.course_controller import _verify_token
    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")

    from src.database import SessionLocal
    from src.models import Course, CourseInfo, Lesson

    session = SessionLocal()
    try:
        course = session.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
        if not course:
            raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
        info = session.query(CourseInfo).filter(CourseInfo.course_info_id == course.course_info_id).first()
        lessons = (
            session.query(Lesson.lesson_id, Lesson.title, Lesson.finish)
            .filter(Lesson.course_id == course.course_id)
            .order_by(Lesson.created_at.asc())
            .all()
        )
        lesson_models = [LessonInfo(lesson_id=l.lesson_id, title=l.title, finish=l.finish) for l in lessons]

        course_full = CourseFullInfo(
            title=info.title if info else "",
            description=info.description if info else "",
            duration=info.duration if info else 0,
            roadmap=info.roadmap if info else None,
            lesson=lesson_models,
            updated_at=course.updated_at.isoformat() if course.updated_at else "",
        )
        return CourseFullInfoResponse(status=200, info=course_full)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error fetching course")
    finally:
        session.close()


@router.get("/all", response_model=CourseListResponse)
async def get_all_user_courses(request: Request, _auth=Depends(require_bearer)):
    """Return summary list of all courses for the authenticated user."""
    from src.controllers.course_controller import _verify_token
    user_id = _verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Bạn không thể truy cập khóa học của người khác")

    from src.database import SessionLocal
    from src.models import Course, CourseInfo, Lesson

    session = SessionLocal()
    try:
        rows = (
            session.query(
                Course.course_id,
                Course.updated_at,
                CourseInfo.title,
                CourseInfo.description,
                CourseInfo.duration,
            )
            .join(CourseInfo, Course.course_info_id == CourseInfo.course_info_id)
            .filter(Course.user_id == user_id)
            .all()
        )
        course_ids = [r.course_id for r in rows]
        lesson_counts = {cid: 0 for cid in course_ids}
        finish_counts = {cid: 0 for cid in course_ids}
        if course_ids:
            lessons = (
                session.query(Lesson.course_id, Lesson.finish).filter(Lesson.course_id.in_(course_ids)).all()
            )
            for cid, fin in lessons:
                lesson_counts[cid] = lesson_counts.get(cid, 0) + 1
                if fin:
                    finish_counts[cid] = finish_counts.get(cid, 0) + 1

        summaries = [
            CourseSummary(
                course_id=r.course_id,
                title=r.title or "",
                description=r.description or "",
                duration=r.duration or 0,
                lesson_num=lesson_counts.get(r.course_id, 0),
                finish_lesson_num=finish_counts.get(r.course_id, 0),
                updated_at=r.updated_at.isoformat() if r.updated_at else "",
            )
            for r in rows
        ]
        return CourseListResponse(status=200, courses=summaries)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error fetching courses")
    finally:
        session.close()
