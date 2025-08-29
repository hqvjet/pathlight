from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import secrets
import uuid
from datetime import datetime
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

import boto3
import httpx
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from src.config import config

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
ALLOWED_DOC_EXTS = {".pdf", ".pptx", ".docx", ".doc"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB
DEFAULT_REGION = "ap-northeast-1"


# -------------------------------------------------------------------
# Types
# -------------------------------------------------------------------
class AuthResult(NamedTuple):
    user_id: Optional[str]
    token: Optional[str]


# -------------------------------------------------------------------
# Lazy imports for DB models
# -------------------------------------------------------------------
def _lazy_models():
    """Delay heavy ORM imports until needed (avoids circular imports)."""
    try:
        from src.database import SessionLocal as _SL  # type: ignore
        from src.models import (  # type: ignore
            Course as _C,
            CourseInfo as _CI,
            UnderstandLevelTag as _UL,
            Lesson as _L,
            Test as _T,
            LessonQA as _LQA,
            FinalTest as _FT,
            FinalQA as _FQA,
        )
        return _SL, _C, _CI, _UL, _L, _T, _LQA, _FT, _FQA
    except ImportError as e:
        logger.error(f"Failed to import models: {e}")
        raise


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _json(status: int, message: str, **extra) -> JSONResponse:
    """Consistent JSON envelope."""
    payload = {"status": status, "message": message}
    payload.update(extra)
    return JSONResponse(status_code=status, content=payload)


def _decode(request: Request) -> AuthResult:
    """Decode JWT from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return AuthResult(None, None)

    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return AuthResult(payload.get("sub"), token)
    except JWTError as e:
        logger.debug(f"JWT decode failed: {e}")
        return AuthResult(None, None)


def _get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=getattr(config, "ACCESS_KEY_ID", None) or None,
        aws_secret_access_key=getattr(config, "SECRET_ACCESS_KEY", None) or None,
        region_name=getattr(config, "REGION", None) or None,
    )


def _encrypted_filename(user_id: str, original_name: str) -> str:
    """Generate a deterministic-but-salted encrypted filename, preserving extension."""
    ext = ""
    if "." in original_name:
        ext = "." + original_name.rsplit(".", 1)[1].lower()

    salt = secrets.token_hex(8)
    safe_name = html.escape(original_name)
    seed = f"{user_id}|{safe_name}|{datetime.utcnow().isoformat()}|{salt}"
    digest = hashlib.sha256(seed.encode()).hexdigest()
    numeric = str(int(digest, 16) % 10**12).zfill(12)
    return f"{numeric}{ext}"


def _s3_error(exc: Exception) -> JSONResponse:
    """Map common boto3 errors to friendly messages."""
    if isinstance(exc, EndpointConnectionError):
        return _json(500, "Cannot connect to S3 endpoint.")
    if isinstance(exc, NoCredentialsError):
        return _json(401, "Credentials missing.")
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchBucket", "404", "NotFound"}:
            return _json(500, "S3 bucket not found.")
        if code in {"403", "Forbidden"}:
            return _json(403, "Access denied to S3 bucket.")
        if code in {"301", "PermanentRedirect", "AuthorizationHeaderMalformed"}:
            return _json(500, "S3 region mismatch.")
        return _json(500, f"S3 error: {code or 'unknown'}")
    return _json(500, "S3 error")


def _error_response(phase: str, backend_error: Optional[str]) -> JSONResponse:
    """Hide internal errors unless verbose mode is enabled."""
    verbose = str(os.getenv("COURSE_VERBOSE_ERRORS", "")).lower() in {"1", "true", "yes"} or bool(os.getenv("DEBUG"))
    if backend_error and verbose:
        return _json(500, f"{phase} failed", detail=backend_error)
    return _json(401, "Có lỗi xảy ra, xin vui lòng thử lại")


# -------------------------------------------------------------------
# Upload
# -------------------------------------------------------------------
async def upload_files_docs(request: Request, files: List[UploadFile]) -> JSONResponse:
    """Upload documents to S3 after validating type and size."""
    auth_result = _decode(request)
    if not auth_result.user_id:
        return _json(401, "Unauthorized")

    if not files:
        return _json(400, "Không có file nào được gửi lên")

    total = 0
    staged: List[Tuple[UploadFile, bytes, str]] = []

    for f in files:
        name = f.filename or ""
        ext = "." + name.rsplit(".", 1)[1].lower() if "." in name else ""
        if ext not in ALLOWED_DOC_EXTS:
            return _json(400, "Định dạng file không được hỗ trợ")

        body = await f.read()
        total += len(body)
        if total > MAX_UPLOAD_BYTES:
            return _json(400, "File vượt quá dung lượng giới hạn, xin vui lòng xem lại")

        staged.append((f, body, _encrypted_filename(auth_result.user_id, name)))

    bucket = getattr(config, "S3_BUCKET_NAME", None)
    if not bucket:
        return _json(500, "S3_BUCKET_NAME is not configured")

    s3 = _get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket)
    except (EndpointConnectionError, NoCredentialsError, ClientError) as e:
        return _s3_error(e)

    uploaded: List[str] = []
    for f, body, key in staged:
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType=f.content_type or "application/octet-stream",
            )
            uploaded.append(key)
        except (EndpointConnectionError, NoCredentialsError, ClientError) as e:
            return _s3_error(e)

    return _json(200, "Uploaded successfully", uploaded_file=uploaded)


# -------------------------------------------------------------------
# Create course
# -------------------------------------------------------------------
async def create_course(request: Request, payload: Dict[str, Any]) -> JSONResponse:
    """Create course: validate → call agentic (vectorize/generate) → persist DB."""
    auth_result = _decode(request)
    if not auth_result.user_id or not auth_result.token:
        return _json(401, "Unauthorized")

    valid, err_resp, fields = _validate_create_course_payload(payload)
    if not valid:
        return err_resp if err_resp is not None else _json(400, "Invalid payload")
    title, description, understand_level, duration, uploaded_files = fields  # type: ignore

    course_id, course_info_id = str(uuid.uuid4()), str(uuid.uuid4())

    ok_v, err_v = await _call_vectorize(course_id, uploaded_files, auth_result.token)
    if not ok_v:
        return _error_response("vectorize", err_v)

    ok_g, err_g = await _call_generate(course_id, understand_level, duration, auth_result.token)
    if not ok_g:
        return _error_response("generate", err_g)

    if not _persist_course(
        course_id=course_id,
        course_info_id=course_info_id,
        user_id=auth_result.user_id,
        title=title,
        description=description,
        understand_level=understand_level,
        duration=duration,
    ):
        return _error_response("persist", "db_persist_failed")

    return _json(200, "Đã tạo khóa học thành công")


def _validate_create_course_payload(
    payload: Dict[str, Any],
) -> Tuple[bool, Optional[JSONResponse], Optional[Tuple[str, str, str, int, List[str]]]]:
    title = payload.get("title")
    description = payload.get("description")
    understand_level = payload.get("understand_level")
    duration = payload.get("duration")
    uploaded_files = payload.get("uploaded_file")

    if not uploaded_files or not isinstance(uploaded_files, list):
        return False, _json(400, "Không tìm thấy file, xin vui lòng thử lại"), None

    if not title or not description or not understand_level or not duration:
        return False, _json(400, "Thiếu thông tin bắt buộc"), None

    try:
        duration_int = int(duration)
    except Exception:
        return False, _json(400, "Trường 'duration' phải là số nguyên (giờ)"), None

    return True, None, (str(title), str(description), str(understand_level), duration_int, list(uploaded_files))


# -------------------------------------------------------------------
# Agentic calls
# -------------------------------------------------------------------
async def _call_vectorize(course_id: str, uploaded_files: List[str], token: str) -> Tuple[bool, Optional[str]]:
    vectorize_url = f"{config.AGENTIC_SERVICE_ENDPOINT}"
    payload = {"id": course_id, "category": 0, "uploaded_file": uploaded_files}
    return await _post_agentic(vectorize_url, payload, token, phase="vectorize")


async def _call_generate(course_id: str, understand_level: str, duration_hours: int, token: str) -> Tuple[bool, Optional[str]]:
    generate_url = f"{config.AGENTIC_SERVICE_ENDPOINT}"
    payload = {"id": course_id, "difficulty": understand_level, "duration": duration_hours * 60}
    return await _post_agentic(generate_url, payload, token, phase="generate")


async def _post_agentic(url: str, payload: Dict[str, Any], token: str, phase: str) -> Tuple[bool, Optional[str]]:
    """POST to agentic service (optionally with SigV4). Returns (ok, error_msg)."""
    use_sigv4 = str(os.getenv("AGENTIC_EXPECT_SIGV4", "")).lower() in {"1", "true", "yes"}
    default_timeout = 60 if phase == "vectorize" else 120
    try:
        timeout = int(os.getenv("COURSE_AGENTIC_TIMEOUT_SECONDS", "") or default_timeout)
    except ValueError:
        timeout = default_timeout

    body = json.dumps(payload)
    headers: Dict[str, str] = {"Content-Type": "application/json", "X-User-Token": token}

    if use_sigv4:
        try:
            from botocore.auth import SigV4Auth  # lazy import
            from botocore.awsrequest import AWSRequest
            from botocore.credentials import Credentials

            region = os.getenv("REGION", getattr(config, "REGION", DEFAULT_REGION))
            access_key = os.getenv("AWS_ACCESS_KEY_ID")
            secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            if not access_key or not secret_key:
                return False, "Missing AWS credentials"

            creds = Credentials(access_key, secret_key, os.getenv("AWS_SESSION_TOKEN"))
            aws_req = AWSRequest(method="POST", url=url, data=body, headers={"Content-Type": "application/json"})
            SigV4Auth(creds, "lambda", region).add_auth(aws_req)
            headers.update(dict(aws_req.headers))
        except Exception as e:
            logger.error(f"SigV4 auth failed: {e}")
            return False, str(e)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, content=body, headers=headers)
    except httpx.TimeoutException:
        return False, f"timeout after {timeout}s"
    except Exception as e:
        logger.error(f"HTTP request failed: {e}")
        return False, str(e)

    if resp.status_code != 200:
        return False, f"status={resp.status_code} body={resp.text[:400]}"

    return True, None


# -------------------------------------------------------------------
# Persistence
# -------------------------------------------------------------------
def _persist_course(
    course_id: str,
    course_info_id: str,
    user_id: str,
    title: str,
    description: str,
    understand_level: str,
    duration: int,
) -> bool:
    """Persist course & course_info. Returns True on success."""
    if str(os.getenv("COURSE_SERVICE_SKIP_DB", "")).lower() in {"1", "true", "yes"}:
        return True

    SessionLocal, Course, CourseInfo, UnderstandLevelTag, *_ = _lazy_models()
    session = SessionLocal()
    try:
        level = session.query(UnderstandLevelTag).filter_by(understand_level=understand_level).first()
        if not level:
            level = UnderstandLevelTag(
                understand_level_id=str(uuid.uuid4()),
                understand_level=understand_level,
            )
            session.add(level)
            session.flush()

        if not title or not description:
            logger.error("Course title or description is missing.")
            session.rollback()
            return False

        info = CourseInfo(
            course_info_id=course_info_id,
            understand_level_id=level.understand_level_id,
            title=title,
            description=description,
            duration=duration,
            roadmap=None,
        )
        course = Course(
            course_id=course_id,
            course_info_id=info.course_info_id,
            user_id=user_id,
            finish=False,
        )

        session.add(info)
        session.add(course)
        session.commit()
        return True
    except Exception as e:
        logger.exception(f"Database operation failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()


# -------------------------------------------------------------------
# Delete APIs
# -------------------------------------------------------------------
def _unauth_delete_response() -> JSONResponse:
    return _json(401, "Bạn chưa xác thực hoặc phiên đăng nhập đã hết hạn")


async def delete_single_course(request: Request, course_id: Optional[str]) -> JSONResponse:
    """Delete one course of the authenticated user (and its related data)."""
    auth = _decode(request)
    if not auth.user_id:
        return _unauth_delete_response()
    if not course_id:
        return _json(400, "Thiếu course_id")

    SessionLocal, Course, CourseInfo, _, Lesson, Test, LessonQA, FinalTest, FinalQA = _lazy_models()
    session = SessionLocal()
    try:
        course = session.query(Course).filter_by(course_id=course_id, user_id=auth.user_id).first()
        if not course:
            return _json(404, "Không tìm thấy khóa học")

        # collect related ids
        lesson_ids = [lid for (lid,) in session.query(Lesson.lesson_id).filter(Lesson.course_id == course.course_id).all()]
        test_ids = (
            [tid for (tid,) in session.query(Test.test_id).filter(Test.lesson_id.in_(lesson_ids)).all()]
            if lesson_ids
            else []
        )
        final_test_ids = [
            ftid for (ftid,) in session.query(FinalTest.final_test_id).filter(FinalTest.course_id == course.course_id).all()
        ]

        # delete children first
        if test_ids:
            session.query(LessonQA).filter(LessonQA.test_id.in_(test_ids)).delete(synchronize_session=False)
        if final_test_ids:
            session.query(FinalQA).filter(FinalQA.final_test_id.in_(final_test_ids)).delete(synchronize_session=False)
        if test_ids:
            session.query(Test).filter(Test.test_id.in_(test_ids)).delete(synchronize_session=False)
        if final_test_ids:
            session.query(FinalTest).filter(FinalTest.final_test_id.in_(final_test_ids)).delete(synchronize_session=False)
        if lesson_ids:
            session.query(Lesson).filter(Lesson.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)

        # remove course & possibly orphaned CourseInfo
        course_info_id = course.course_info_id
        session.delete(course)
        still = session.query(Course).filter(Course.course_info_id == course_info_id).first()
        if not still:
            session.query(CourseInfo).filter(CourseInfo.course_info_id == course_info_id).delete(synchronize_session=False)

        session.commit()
        return _json(200, "Đã xóa khóa học thành công")
    except Exception as e:
        logger.error("delete_single_course error user=%s course=%s err=%s", auth.user_id, course_id, e)
        session.rollback()
        return _json(500, "Xóa khóa học thất bại")
    finally:
        session.close()


async def delete_all_courses(request: Request) -> JSONResponse:
    """Delete all courses belonging to the authenticated user."""
    auth = _decode(request)
    if not auth.user_id:
        return _json(401, "Bạn không có quyền xóa khóa học của người khác")

    SessionLocal, Course, CourseInfo, _, Lesson, Test, LessonQA, FinalTest, FinalQA = _lazy_models()
    session = SessionLocal()
    try:
        courses = session.query(Course).filter(Course.user_id == auth.user_id).all()
        if not courses:
            return _json(200, "Đã xóa toàn bộ khóa học thành công")

        course_ids = [c.course_id for c in courses]
        course_info_ids = [c.course_info_id for c in courses]

        lesson_ids = [lid for (lid,) in session.query(Lesson.lesson_id).filter(Lesson.course_id.in_(course_ids)).all()]
        test_ids = (
            [tid for (tid,) in session.query(Test.test_id).filter(Test.lesson_id.in_(lesson_ids)).all()]
            if lesson_ids
            else []
        )
        final_test_ids = [
            fid for (fid,) in session.query(FinalTest.final_test_id).filter(FinalTest.course_id.in_(course_ids)).all()
        ]

        if test_ids:
            session.query(LessonQA).filter(LessonQA.test_id.in_(test_ids)).delete(synchronize_session=False)
        if final_test_ids:
            session.query(FinalQA).filter(FinalQA.final_test_id.in_(final_test_ids)).delete(synchronize_session=False)
        if test_ids:
            session.query(Test).filter(Test.test_id.in_(test_ids)).delete(synchronize_session=False)
        if final_test_ids:
            session.query(FinalTest).filter(FinalTest.final_test_id.in_(final_test_ids)).delete(synchronize_session=False)
        if lesson_ids:
            session.query(Lesson).filter(Lesson.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)

        session.query(Course).filter(Course.course_id.in_(course_ids), Course.user_id == auth.user_id).delete(
            synchronize_session=False
        )

        # clean orphaned CourseInfo
        for ci in course_info_ids:
            still = session.query(Course).filter(Course.course_info_id == ci).first()
            if not still:
                session.query(CourseInfo).filter(CourseInfo.course_info_id == ci).delete(synchronize_session=False)

        session.commit()
        return _json(200, "Đã xóa toàn bộ khóa học thành công")
    except Exception as e:
        logger.error("delete_all_courses error user=%s err=%s", auth.user_id, e)
        session.rollback()
        return _json(500, "Xóa toàn bộ khóa học thất bại")
    finally:
        session.close()
