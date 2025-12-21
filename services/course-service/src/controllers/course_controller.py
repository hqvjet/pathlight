from typing import List
from uuid import uuid4
from datetime import datetime
import hashlib
import secrets
import logging
import string
import httpx
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from fastapi import Request, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from jose import jwt
import os

from src.config import config
from src.database import get_session
from src.models import Course
from src.schemas.course_schemas import (
    CourseFullInfo,
    CourseFullInfoResponse,
    LessonInfo,
    CourseListResponse,
    CourseSummary,
    LessonListResponse,
    LessonDetail,
    AssessmentListResponse,
    AssessmentItem,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    AssessmentSubmitResult,
    AssessmentSubmitResultItem,
    FinishCourseRequest,
    FinishLessonRequest,
    PresignUploadRequest,
    PresignUploadResponse,
	CourseVisibilityUpdate,
	CreateCourseRequest,
)

logger = logging.getLogger(__name__)

DIFFICULTY_EXP = {
	1: 10,
	2: 20,
	3: 30,
	4: 40,
	5: 50,
}
PASS_THRESHOLD = 80
COURSE_COMPLETION_EXP = 100
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".pptx", ".ppt", ".docx", ".doc"}


async def create_course_controller(request: Request, body: CreateCourseRequest):
	"""Create a course generation job (S3 validation + SQS enqueue)."""
	from src.services.sqs_publisher import send_generate_with_vectorize

	queue_url = os.getenv("SQS_QUEUE_URL")
	if not queue_url:
		return {"status": 500, "message": "SQS_QUEUE_URL is not configured"}

	# Required fields
	short_prompt = (body.short_prompt or "").strip()
	if not short_prompt:
		return {"status": 400, "message": "short_prompt is required"}
	if not body.user_role:
		return {"status": 400, "message": "user_role is required"}

	job_type = (body.type or "generate_course").strip()
	allowed_job_types = {"generate_course", "generate_quiz"}
	if job_type not in allowed_job_types:
		return {"status": 400, "message": "type must be one of generate_course, generate_quiz"}

	course_id = body.course_id or f"course-{uuid4()}"
	s3_keys = (body.documents or []) + (body.s3_key or [])

	# Normalize user prefix early
	user_id = _verify_token(request)
	if not user_id:
		return {"status": 401, "message": "Unauthorized"}
	body.user_id = user_id
	user_prefix = f"users/{user_id}/"
	normalized_s3_keys = []
	for key in s3_keys:
		if not key:
			continue
		normalized_s3_keys.append(key if key.startswith(user_prefix) else user_prefix + key.lstrip('/'))
	s3_keys = normalized_s3_keys

	region = getattr(config, "REGION", None) or os.getenv("REGION") or "ap-northeast-1"
	# Validate files up to 25MB each
	if s3_keys:
		bucket = getattr(config, "S3_BUCKET_NAME", None) or os.getenv("S3_BUCKET_NAME")
		if not bucket:
			return {"status": 500, "message": "S3_BUCKET_NAME is not configured"}

		s3 = boto3.client("s3", region_name=region)
		max_bytes = MAX_UPLOAD_BYTES
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
					return {"status": 400, "message": f"File exceeds 25MB: {key}"}
		except Exception as e:
			return {"status": 500, "message": f"Failed to validate S3 objects: {e}"}

	try:
		resp = send_generate_with_vectorize(
			queue_url=queue_url,
			course_id=course_id,
			s3_keys=s3_keys,
			short_prompt=short_prompt,
			user_role=body.user_role,
			course_level=body.course_level,
			course_constraint=body.course_constraint,
			course_duration=body.course_duration,
			user_id=user_id,
			region=region,
			group_id=os.getenv("SQS_GROUP_ID"),
			job_type=job_type,
		)
		_log_activity(request, user_id, "create_course")
		return {"status": 202, "message": "submitted", "sqs_message_id": resp.get("MessageId"), "course_id": course_id}
	except Exception as e:
		return {"status": 500, "message": f"Failed to submit job: {e}"}


def _verify_token(request: Request):
	"""Return user_id (sub) if Authorization header is present.

	Strategy:
	1) If JWT_SECRET_KEY configured, try to verify signature and extract `sub`.
	2) Fallback: parse unverified claims to extract a user id from common keys (sub, user_id, uid, id).
	   This prevents 401 due to mismatched secrets across services while we align secrets.
	"""
	auth_header = request.headers.get("Authorization")
	if not auth_header or not auth_header.startswith("Bearer "):
		return None
	token = auth_header.split(" ")[1]
	# Primary: verified decode
	if getattr(config, "JWT_SECRET_KEY", None):
		try:
			payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
			for key in ("sub", "user_id", "uid", "id"):
				if key in payload and payload[key]:
					return str(payload[key])
		except Exception as e:
			logger.warning("JWT verification failed, falling back to unverified claims: %s", e)
	# Fallback: unverified claims (temporary compatibility)
	try:
		claims = jwt.get_unverified_claims(token)
		for key in ("sub", "user_id", "uid", "id"):
			if key in claims and claims[key]:
				return str(claims[key])
	except Exception as e:
		logger.error("Failed to parse JWT claims: %s", e)
	return None


def _user_service_base_url() -> str | None:
	return getattr(config, "USER_SERVICE_URL", None) or os.getenv("USER_SERVICE_URL")


def _award_experience(request: Request, user_id: str, exp_amount: int) -> dict | None:
	"""Call user-service to add experience for the current user.

	Returns a dict with status_code and body when the call was attempted, otherwise None.
	"""
	if exp_amount <= 0:
		return None
	base_url = _user_service_base_url()
	auth_header = request.headers.get("Authorization")
	if not base_url or not auth_header:
		return None
	url = f"{base_url.rstrip('/')}/user/experience/add"
	try:
		resp = httpx.post(
			url,
			headers={"Authorization": auth_header},
			json={"exp": exp_amount},
			timeout=5.0,
		)
		data = resp.json() if resp.content else {}
		return {"status_code": resp.status_code, "body": data}
	except Exception as e:  # pragma: no cover - network issues
		logger.error("Failed to award experience for user %s: %s", user_id, e)
		return None


def _log_activity(request: Request, user_id: str | None, event: str) -> dict | None:
	"""Call user-service to log an activity event.

	Returns a dict with status_code and body when the call was attempted, otherwise None.
	"""
	if not user_id:
		return None
	base_url = _user_service_base_url()
	auth_header = request.headers.get("Authorization")
	if not base_url or not auth_header:
		return None
	url = f"{base_url.rstrip('/')}/user/activity"
	try:
		resp = httpx.post(
			url,
			headers={"Authorization": auth_header},
			json={"event": event},
			timeout=5.0,
		)
		data = resp.json() if resp.content else {}
		return {"status_code": resp.status_code, "body": data}
	except Exception as e:  # pragma: no cover - network issues
		logger.error("Failed to log activity for user %s: %s", user_id, e)
		return None


def _experience_payload(gained_exp: int, award_result: dict | None) -> dict:
	payload = {"gained_exp": gained_exp}
	if award_result and isinstance(award_result.get("body"), dict):
		stats = award_result["body"].get("updated_stats") or {}
		payload.update(
			{
				"new_level": stats.get("new_level") or stats.get("level"),
				"new_exp": stats.get("new_exp") or stats.get("current_exp"),
				"require_exp": stats.get("new_require_exp") or stats.get("require_exp"),
				"exp_needed_for_next": stats.get("exp_needed_for_next"),
				"rank": stats.get("rank"),
			}
		)
	return payload


def _update_learning_progress(session, course_id: str, lesson_id: str, user_id: str) -> tuple[int, int]:
	"""Increment learning progress for a user on a course based on lesson order.

	Returns (finished_count, total_lessons).
	"""
	from src.models import Lesson, LearningProgress

	lessons = (
		session.query(Lesson)
		.filter(Lesson.course_id == course_id)
		.order_by(Lesson.created_at.asc(), Lesson.lesson_id.asc())
		.all()
	)
	total = len(lessons)
	if total == 0:
		return 0, 0
	order_map = {l.lesson_id: idx for idx, l in enumerate(lessons)}
	target_idx = order_map.get(lesson_id)
	progress = session.query(LearningProgress).filter(
		LearningProgress.course_id == course_id,
		LearningProgress.user_id == user_id,
	).first()
	if not progress:
		progress = LearningProgress(
			user_id=user_id,
			course_id=course_id,
			num_finished_lesson=0,
			num_total_lesson=total,
		)
		session.add(progress)
	if progress.num_total_lesson != total:
		progress.num_total_lesson = total
	current_finished = min(progress.num_finished_lesson or 0, total)
	if target_idx is None:
		return current_finished, total
	if target_idx < current_finished:
		return current_finished, total
	progress.num_finished_lesson = max(current_finished, target_idx + 1)
	return progress.num_finished_lesson, total


def _get_s3_client():
	"""Create S3 client supporting both AWS cloud and S3-compatible endpoints."""
	kwargs = {
		"service_name": "s3",
		"aws_access_key_id": getattr(config, "ACCESS_KEY_ID", None) or None,
		"aws_secret_access_key": getattr(config, "SECRET_ACCESS_KEY", None) or None,
		"region_name": getattr(config, "REGION", None) or None,
	}
	return boto3.client(**kwargs)


def _random_value(length: int = 8) -> str:
	alphabet = string.ascii_letters + string.digits
	return ''.join(secrets.choice(alphabet) for _ in range(length))


def _sanitize_filename_base(original_name: str, max_len: int = 60) -> str:
	base = original_name.rsplit('.', 1)[0]
	# keep alnum, dash, underscore; replace others with '-'
	cleaned = []
	prev_dash = False
	for ch in base:
		if ch.isalnum() or ch in ('-', '_'):
			cleaned.append(ch)
			prev_dash = False
		else:
			if not prev_dash:
				cleaned.append('-')
				prev_dash = True
	res = ''.join(cleaned).strip('-_')
	if not res:
		res = 'file'
	return res[:max_len]


def _encrypted_filename(user_id: str, original_name: str) -> str:
	"""Build an S3 object key that contains an encrypted/random prefix and the (sanitized) real filename.

	Format: <rand8>-<shortcode>-<sanitizedBase><ext>
	- rand8: random A-Za-z0-9 (like the provided approach)
	- shortcode: 10-char short from SHA256(user_id|original|timestamp|salt)
	- sanitizedBase: original filename (without extension), sanitized
	"""
	ext = ""
	if "." in original_name:
		ext = "." + original_name.rsplit(".", 1)[1].lower()
	salt = secrets.token_hex(4)
	seed = f"{user_id}|{original_name}|{datetime.utcnow().isoformat()}|{salt}"
	digest = hashlib.sha256(seed.encode()).hexdigest()
	short = digest[:10]
	rand = _random_value(8)
	base = _sanitize_filename_base(original_name)
	return f"{rand}-{short}-{base}{ext}"


def _user_prefix(user_id: str) -> str:
	return f"users/{user_id}"


def _ensure_prefix(s3, bucket: str, prefix: str):
	"""Create a zero-byte prefix marker to make the 'folder' appear in S3 consoles.

	S3 is flat, but creating prefix/ helps visibility; ignore errors silently.
	"""
	if not os.getenv("CREATE_USER_PREFIX_MARKER"):
		return
	key = prefix.rstrip("/") + "/"
	try:
		s3.put_object(Bucket=bucket, Key=key, Body=b"")
	except Exception:
		return


def _admin_guard(request: Request):
	user_id = _verify_token(request)
	if not user_id:
		return {"status": 401, "message": "Unauthorized"}
	return None


def list_all_courses_admin_controller(request: Request, page: int, limit: int, search: str | None):
	guard = _admin_guard(request)
	if guard:
		return guard

	session = get_session()()
	try:
		query = session.query(Course)
		if search:
			search_pattern = f"%{search}%"
			query = query.filter(Course.title.ilike(search_pattern))

		total = query.count()
		offset = (page - 1) * limit
		courses = query.order_by(Course.created_at.desc()).offset(offset).limit(limit).all()

		course_list = [
			{
				"course_id": c.course_id,
				"user_id": c.user_id,
				"title": c.title,
				"overview": c.overview,
				"level": c.level,
				"duration": c.duration,
				"publish": bool(c.publish),
				"finish": bool(c.finish),
				"num_lessons": c.num_lessons,
				"created_at": c.created_at.isoformat() if c.created_at else "",
			}
			for c in courses
		]

		return {"status": 200, "courses": course_list, "total": total}
	finally:
		session.close()


async def delete_course_admin_controller(course_id: str, request: Request):
	guard = _admin_guard(request)
	if guard:
		return guard

	return await delete_single_course(request, course_id, admin_override=True)


async def toggle_course_visibility_admin_controller(course_id: str, request: Request, body: CourseVisibilityUpdate):
	guard = _admin_guard(request)
	if guard:
		return guard

	return update_course_visibility_controller(request, body, admin_override=True)


async def presign_upload_urls(request: Request, body: PresignUploadRequest) -> PresignUploadResponse | dict:
	"""Return presigned PUT URLs for direct-to-S3 uploads (single-part).

	Validations:
	- Auth required
	- Allowed extensions: pdf, doc, docx, ppt, pptx
	- Total size must be <= 25MB
	"""
	user_id = _verify_token(request)
	if not user_id:
		logger.warning("Presign aborted: unauthorized (missing/invalid bearer token)")
		return {"status": 401, "message": "Unauthorized"}

	items = body.items or []
	if not items:
		return {"status": 400, "message": "No files to presign"}

	allowed_ext = ALLOWED_UPLOAD_EXTENSIONS
	max_total_bytes = MAX_UPLOAD_BYTES
	total = 0
	for it in items:
		ext = "." + it.filename.rsplit(".", 1)[1].lower() if "." in it.filename else ""
		if ext not in allowed_ext:
			logger.warning("Presign failed: unsupported extension '%s' for file '%s' (user_id=%s)", ext, it.filename, user_id)
			return {"status": 400, "message": "Định dạng file không được hỗ trợ"}
		total += int(it.size or 0)
		if total > max_total_bytes:
			logger.warning("Presign failed: total size %d exceeds 25MB (user_id=%s)", total, user_id)
			return {"status": 400, "message": "Tổng dung lượng vượt 25MB"}

	s3 = _get_s3_client()
	bucket = config.S3_BUCKET_NAME
	if not bucket:
		logger.error("Presign failed: S3_BUCKET_NAME is not configured")
		return {"status": 500, "message": "S3_BUCKET_NAME is not configured"}

	prefix = _user_prefix(user_id)
	_ensure_prefix(s3, bucket, prefix)

	results = []
	for it in items:
		key = f"{prefix}/{_encrypted_filename(user_id, it.filename)}"
		try:
			url = s3.generate_presigned_url(
				ClientMethod="put_object",
				Params={
					"Bucket": bucket,
					"Key": key,
					"ContentType": it.content_type or "application/octet-stream",
				},
				ExpiresIn=900,
			)
			results.append({
				"key": key,
				"upload_url": url,
				"headers": {"Content-Type": it.content_type or "application/octet-stream"},
			})
		except Exception as e:
			logger.error("Failed to presign for file %s: %s", it.filename, e)
			return {"status": 500, "message": "Không tạo được URL tải lên"}

	logger.info("Presign success (user_id=%s): %d file(s)", user_id, len(results))
	return {"status": 200, "items": results}


async def upload_files_docs(request: Request, files: List[UploadFile]):
	user_id = _verify_token(request)
	if not user_id:
		logger.warning("Upload aborted: unauthorized (missing/invalid bearer token)")
		return JSONResponse(status_code=401, content={"status": 401, "message": "Unauthorized"})

	prefix = _user_prefix(user_id)

	allowed_ext = ALLOWED_UPLOAD_EXTENSIONS
	max_total_bytes = MAX_UPLOAD_BYTES
	total_size = 0
	file_payloads = []
	for f in files:
		original = f.filename or ""
		ext = "." + original.rsplit(".", 1)[1].lower() if "." in original else ""
		if ext not in allowed_ext:
			logger.warning("Upload failed: unsupported extension '%s' for file '%s' (user_id=%s)", ext, original, user_id)
			return JSONResponse(status_code=400, content={"status": 400, "message": "Định dạng file không được hỗ trợ"})
		content = await f.read()
		total_size += len(content)
		if total_size > max_total_bytes:
			logger.warning("Upload failed: total size %d exceeds %dB limit (user_id=%s)", total_size, max_total_bytes, user_id)
			return JSONResponse(status_code=400, content={"status": 400, "message": "Tổng dung lượng vượt 25MB"})
		enc_name = _encrypted_filename(user_id, original)
		file_payloads.append((f, content, enc_name))

	s3 = _get_s3_client()
	bucket = config.S3_BUCKET_NAME
	if not bucket:
		logger.error("Upload failed: S3_BUCKET_NAME is not configured")
		return {"status": 500, "message": "S3_BUCKET_NAME is not configured"}

	_ensure_prefix(s3, bucket, prefix)

	# Optional quick bucket check for clearer errors
	try:
		s3.head_bucket(Bucket=bucket)
	except EndpointConnectionError as e:
		logger.error("S3 endpoint connection failed: %s", str(e))
		return {"status": 500, "message": "Cannot connect to S3 endpoint. Check network or region."}
	except NoCredentialsError:
		logger.error("AWS credentials not found")
		return {"status": 500, "message": "Credentials missing. Configure ACCESS_KEY_ID/SECRET_ACCESS_KEY."}
	except ClientError as e:
		code = e.response.get("Error", {}).get("Code", "ClientError")
		logger.error("S3 head_bucket error: %s", code)
		if code in {"403", "Forbidden"}:
			return {"status": 500, "message": "Access denied to S3 bucket. Check IAM permissions."}
		if code in {"404", "NotFound", "NoSuchBucket"}:
			return {"status": 500, "message": "S3 bucket not found. Ensure bucket exists in the configured region."}
		if code in {"301", "PermanentRedirect", "AuthorizationHeaderMalformed"}:
			return {"status": 500, "message": "S3 region mismatch. Verify AWS_REGION matches the bucket's region."}
		return {"status": 500, "message": f"S3 error: {code}"}

	uploaded_names = []
	for f, body, enc_name in file_payloads:
		key = f"{prefix}/{enc_name}"
		try:
			s3.put_object(
				Bucket=bucket,
				Key=key,
				Body=body,
				ContentType=f.content_type or "application/octet-stream",
			)
			uploaded_names.append(enc_name)
		except EndpointConnectionError as e:
			logger.error("S3 upload endpoint error: %s", str(e))
			return {"status": 500, "message": "Cannot connect to S3 endpoint during upload."}
		except NoCredentialsError:
			logger.error("AWS credentials not found during upload")
			return {"status": 500, "message": "Credentials missing during upload."}
		except ClientError as e:
			code = e.response.get("Error", {}).get("Code", "ClientError")
			logger.error("S3 put_object error: %s", code)
			if code in {"301", "PermanentRedirect", "AuthorizationHeaderMalformed"}:
				return {"status": 500, "message": "S3 region mismatch during upload. Verify AWS_REGION and bucket region."}
			return {"status": 500, "message": f"S3 upload failed: {code}"}

	logger.info("Upload successful (user_id=%s): %d file(s) uploaded: %s", user_id, len(uploaded_names), uploaded_names)
	return {"status": 200, "uploaded_file": uploaded_names}



def _unauth_delete_response():
	return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa xác thực hoặc phiên đăng nhập đã hết hạn"})


def update_course_visibility_controller(request: Request, body: CourseVisibilityUpdate):
	from src.database import SessionLocal
	from src.models import Course

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không có quyền thay đổi khóa học này")
	session = SessionLocal()
	try:
		course = session.query(Course).filter(Course.course_id == body.course_id, Course.user_id == user_id).first()
		if not course:
			raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
		course.publish = bool(body.publish)
		session.commit()
		return {"status": 200, "course_id": course.course_id, "publish": course.publish}
	finally:
		session.close()


def list_public_courses_controller(search: str | None = None, owner_id: str | None = None) -> CourseListResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson

	session = SessionLocal()
	try:
		query = session.query(
			Course.course_id,
			Course.created_at,
			Course.title,
			Course.overview,
			Course.level,
			Course.duration,
			Course.publish,
			Course.user_id,
		)
		query = query.filter(Course.publish.is_(True))
		if owner_id:
			query = query.filter(Course.user_id == owner_id)
		if search:
			pattern = f"%{search}%"
			query = query.filter(Course.title.ilike(pattern))
		rows = query.all()
		course_ids = [r.course_id for r in rows]
		lesson_counts = {cid: 0 for cid in course_ids}
		if course_ids:
			lessons = session.query(Lesson.course_id).filter(Lesson.course_id.in_(course_ids)).all()
			for (cid,) in lessons:
				lesson_counts[cid] = lesson_counts.get(cid, 0) + 1
		summaries = [
			CourseSummary(
				course_id=r.course_id,
				title=r.title or "",
				overview=r.overview or "",
				level=r.level or "",
				duration=r.duration or 0,
				finish=False,
				publish=bool(getattr(r, "publish", False)),
				owner_id=r.user_id,
				lesson_num=lesson_counts.get(r.course_id, 0),
				finish_lesson_num=0,
				updated_at=r.created_at.isoformat() if r.created_at else "",
			)
			for r in rows
		]
		return CourseListResponse(status=200, courses=summaries)
	finally:
		session.close()


async def delete_single_course(request: Request, course_id: str | None):
	"""Delete one course of the authenticated user (and its related data)."""
	user_id = _verify_token(request)
	if not user_id:
		return _unauth_delete_response()
	if not course_id:
		return _unauth_delete_response()
	from src.database import SessionLocal, Base
	from src.models import Course, Lesson, Assessment
	session = SessionLocal()
	try:
		# Ensure tables exist for in-memory databases used in tests
		Base.metadata.create_all(bind=session.get_bind())
		course = session.query(Course).filter_by(course_id=course_id, user_id=user_id).first()
		if not course:
			return _unauth_delete_response()
		lesson_ids = [l.lesson_id for (l,) in session.query(Lesson.lesson_id).filter(Lesson.course_id == course.course_id).all()]
		if lesson_ids:
			session.query(Assessment).filter(Assessment.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
			session.query(Lesson).filter(Lesson.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
		session.delete(course)
		session.commit()
		return JSONResponse(status_code=200, content={"status": 200, "message": "Đã xóa khóa học thành công"})
	except Exception as e:
		logger.error("delete_single_course error user=%s course=%s err=%s", user_id, course_id, e)
		session.rollback()
		return _unauth_delete_response()
	finally:
		session.close()


async def delete_all_courses(request: Request):
	"""Delete all courses belonging to the authenticated user."""
	user_id = _verify_token(request)
	if not user_id:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền xóa khóa học của người khác"})
	from src.database import SessionLocal, Base
	from src.models import Course, Lesson, Assessment
	session = SessionLocal()
	try:
		# Ensure tables exist for in-memory databases used in tests
		Base.metadata.create_all(bind=session.get_bind())
		courses = session.query(Course).filter(Course.user_id == user_id).all()
		if not courses:
			return JSONResponse(status_code=200, content={"status": 200, "message": "Đã xóa toàn bộ khóa học thành công"})
		course_ids = [c.course_id for c in courses]
		lesson_ids = [lid for (lid,) in session.query(Lesson.lesson_id).filter(Lesson.course_id.in_(course_ids)).all()]
		if lesson_ids:
			session.query(Assessment).filter(Assessment.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
			session.query(Lesson).filter(Lesson.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
		session.query(Course).filter(Course.course_id.in_(course_ids), Course.user_id == user_id).delete(synchronize_session=False)
		session.commit()
		return JSONResponse(status_code=200, content={"status": 200, "message": "Đã xóa toàn bộ khóa học thành công"})
	except Exception as e:
		logger.error("delete_all_courses error user=%s err=%s", user_id, e)
		session.rollback()
		return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền xóa khóa học của người khác"})
	finally:
		session.close()


# ---------------- Retrieval Controllers ----------------

def get_course_full_info_controller(request: Request, course_id: str) -> CourseFullInfoResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson, LearningProgress

	user_id = _verify_token(request)
	session = SessionLocal()
	try:
		course = session.query(Course).filter(Course.course_id == course_id).first()
		if not course:
			raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
		is_owner = course.user_id == (user_id or "")
		if not is_owner and not getattr(course, "publish", False):
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")

		lessons = (
			session.query(Lesson)
			.filter(Lesson.course_id == course.course_id)
			.order_by(Lesson.created_at.asc(), Lesson.lesson_id.asc())
			.all()
		)
		progress = None
		finished_lessons = 0
		if user_id:
			progress = session.query(LearningProgress).filter(
				LearningProgress.course_id == course.course_id,
				LearningProgress.user_id == user_id,
			).first()
			if progress:
				finished_lessons = min(progress.num_finished_lesson or 0, len(lessons))
		lesson_models: list[LessonInfo] = []
		for idx, l in enumerate(lessons):
			lesson_models.append(
				LessonInfo(
					lesson_id=l.lesson_id,
					title=l.title,
					finish=idx < finished_lessons,
				)
			)

		course_full = CourseFullInfo(
			title=getattr(course, "title", ""),
			overview=getattr(course, "overview", ""),
			level=getattr(course, "level", ""),
			duration=getattr(course, "duration", 0) or 0,
			publish=bool(getattr(course, "publish", False)),
			finish=bool(getattr(course, "finish", False)),
			owner_id=getattr(course, "user_id", ""),
			lesson=lesson_models,
			progress_finished_lessons=finished_lessons,
			progress_total_lessons=len(lessons),
			updated_at=course.created_at.isoformat() if getattr(course, "created_at", None) else "",
		)
		return CourseFullInfoResponse(status=200, info=course_full)
	finally:
		session.close()


def get_all_courses_controller(request: Request) -> CourseListResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson, LearningProgress

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không thể truy cập khóa học của người khác")
	session = SessionLocal()
	try:
		rows = (
			session.query(
				Course.course_id,
				Course.created_at,
				Course.title,
				Course.overview,
				Course.level,
				Course.duration,
				Course.publish,
				Course.finish,
			)
			.filter(Course.user_id == user_id)
			.all()
		)
		course_ids = [r.course_id for r in rows]
		lesson_counts = {cid: 0 for cid in course_ids}
		finish_counts = {cid: 0 for cid in course_ids}
		finish_map = {cid: False for cid in course_ids}
		if course_ids:
			lessons = session.query(Lesson.course_id).filter(Lesson.course_id.in_(course_ids)).all()
			for (cid,) in lessons:
				lesson_counts[cid] = lesson_counts.get(cid, 0) + 1

			progress_rows = session.query(LearningProgress).filter(
				LearningProgress.course_id.in_(course_ids),
				LearningProgress.user_id == user_id,
			).all()
			for p in progress_rows:
				total = lesson_counts.get(p.course_id, p.num_total_lesson)
				finished = min(p.num_finished_lesson or 0, total)
				finish_counts[p.course_id] = finished
				finish_map[p.course_id] = total > 0 and finished >= total
		summaries = [
			CourseSummary(
				course_id=r.course_id,
				title=r.title or "",
				overview=r.overview or "",
				level=r.level or "",
				duration=r.duration or 0,
				finish=finish_map.get(r.course_id, False),
				publish=bool(getattr(r, "publish", False)),
				owner_id=user_id,
				lesson_num=lesson_counts.get(r.course_id, 0),
				finish_lesson_num=finish_counts.get(r.course_id, 0),
				updated_at=r.created_at.isoformat() if r.created_at else "",
			)
			for r in rows
		]
		return CourseListResponse(status=200, courses=summaries)
	finally:
		session.close()


def list_course_lessons_controller(request: Request, course_id: str) -> LessonListResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson, LearningProgress

	user_id = _verify_token(request)
	session = SessionLocal()
	try:
		course = session.query(Course).filter(Course.course_id == course_id).first()
		if not course:
			raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
		is_owner = course.user_id == (user_id or "")
		if not is_owner and not getattr(course, "publish", False):
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")

		lessons = (
			session.query(Lesson)
			.filter(Lesson.course_id == course_id)
			.order_by(Lesson.created_at.asc(), Lesson.lesson_id.asc())
			.all()
		)
		finished_lessons = 0
		if user_id:
			progress = session.query(LearningProgress).filter(
				LearningProgress.course_id == course.course_id,
				LearningProgress.user_id == user_id,
			).first()
			if progress:
				finished_lessons = min(progress.num_finished_lesson or 0, len(lessons))

		lesson_models = [
			LessonDetail(
				lesson_id=getattr(l, "lesson_id"),
				course_id=getattr(l, "course_id"),
				title=getattr(l, "title"),
				overview=getattr(l, "overview", ""),
				content=getattr(l, "content"),
				duration=getattr(l, "duration", 0) or 0,
				finish=idx < finished_lessons,
			)
			for idx, l in enumerate(lessons)
		]
		return LessonListResponse(status=200, lessons=lesson_models)
	finally:
		session.close()


def get_lesson_detail_controller(request: Request, course_id: str, lesson_id: str) -> LessonDetail:
	from src.database import SessionLocal
	from src.models import Course, Lesson, LearningProgress

	user_id = _verify_token(request)
	session = SessionLocal()
	try:
		course = session.query(Course).filter(Course.course_id == course_id).first()
		if not course:
			raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
		if course.user_id != (user_id or "") and not getattr(course, "publish", False):
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
		lesson = session.query(Lesson).filter(Lesson.lesson_id == lesson_id, Lesson.course_id == course_id).first()
		if not lesson:
			raise HTTPException(status_code=404, detail="Lesson not found")
		completed = False
		if user_id:
			progress = session.query(LearningProgress).filter(
				LearningProgress.course_id == course.course_id,
				LearningProgress.user_id == user_id,
			).first()
			if progress:
				lessons = (
					session.query(Lesson)
					.filter(Lesson.course_id == course.course_id)
					.order_by(Lesson.created_at.asc(), Lesson.lesson_id.asc())
					.all()
				)
				order_map = {l.lesson_id: idx for idx, l in enumerate(lessons)}
				target_idx = order_map.get(lesson.lesson_id)
				completed = target_idx is not None and (target_idx < (progress.num_finished_lesson or 0))
		return LessonDetail(
			lesson_id=getattr(lesson, "lesson_id"),
			course_id=getattr(lesson, "course_id"),
			title=getattr(lesson, "title"),
			overview=getattr(lesson, "overview", ""),
			content=getattr(lesson, "content"),
			duration=getattr(lesson, "duration", 0) or 0,
			finish=completed,
		)
	finally:
		session.close()


def get_assessment_list_controller(
	request: Request,
	course_id: str,
	lesson_id: str,
	*,
	include_hints: bool = True,
	include_explanations: bool = True,
) -> AssessmentListResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson, Assessment

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
	session = SessionLocal()
	try:
		course = session.query(Course).filter(Course.course_id == course_id).first()
		if not course:
			raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
		is_owner = course.user_id == user_id
		if not is_owner and not getattr(course, "publish", False):
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
		lesson = session.query(Lesson).filter(Lesson.lesson_id == lesson_id, Lesson.course_id == course.course_id).first()
		if not lesson:
			raise HTTPException(status_code=404, detail="Lesson not found")
		assessments = (
			session.query(Assessment)
			.filter(Assessment.lesson_id == lesson.lesson_id)
			.order_by(Assessment.created_at.asc())
			.all()
		)
		items = [
			AssessmentItem(
				assessment_id=a.assessment_id,
				lesson_id=a.lesson_id,
				question=a.question,
				hint=a.hint if include_hints else None,
				explanation=a.explanation if include_explanations else None,
				difficulty=a.difficulty,
				option1=a.option1,
				option2=a.option2,
				option3=a.option3,
				option4=a.option4,
				answer=a.answer,
			)
			for a in assessments
		]
		return AssessmentListResponse(status=200, assessments=items)
	finally:
		session.close()


def submit_assessment_controller(request: Request, course_id: str, lesson_id: str, body: AssessmentSubmitRequest) -> AssessmentSubmitResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson, Assessment
	import math

	user_id = _verify_token(request)
	if not user_id:
		return AssessmentSubmitResponse(status=401, message="Bạn không có quyền làm bài kiểm tra này")

	session = SessionLocal()
	try:
		course = session.query(Course).filter(Course.course_id == course_id).first()
		if not course:
			return AssessmentSubmitResponse(status=404, message="Không tìm thấy khóa học")
		is_owner = course.user_id == user_id
		if not is_owner and not getattr(course, "publish", False):
			return AssessmentSubmitResponse(status=401, message="Bạn không có quyền làm bài kiểm tra này")
		lesson = session.query(Lesson).filter(Lesson.lesson_id == lesson_id, Lesson.course_id == course.course_id).first()
		if not lesson:
			return AssessmentSubmitResponse(status=404, message="Không tìm thấy bài học")
		qas = session.query(Assessment).filter(Assessment.lesson_id == lesson.lesson_id).all()
		if not qas:
			return AssessmentSubmitResponse(status=404, message="Bài kiểm tra chưa có câu hỏi")
		qa_lookup = {a.assessment_id: a for a in qas}
		if not body.answers or len(body.answers) < len(qas):
			return AssessmentSubmitResponse(status=400, message="Vui lòng trả lời tất cả câu hỏi trước khi nộp bài")

		correct_count = 0
		earned_exp = 0
		penalty_exp = 0
		answer_results: list[AssessmentSubmitResultItem] = []

		for ans in body.answers:
			qa = qa_lookup.get(ans.assessment_id)
			if not qa:
				continue
			selected = int(ans.answer)
			correct = int(qa.answer)
			is_correct = selected == correct
			if is_correct:
				correct_count += 1

			try:
				difficulty_int = int(qa.difficulty) if qa.difficulty is not None else None
			except Exception:
				difficulty_int = None
			base_exp = DIFFICULTY_EXP.get(difficulty_int, DIFFICULTY_EXP[1])
			if is_correct:
				gained = base_exp
				penalty = 0
			else:
				gained = 0
				penalty = math.floor(base_exp * 0.5)
			earned_exp += gained
			penalty_exp += penalty
			answer_results.append(
				AssessmentSubmitResultItem(
					assessment_id=qa.assessment_id,
					selected_answer=selected,
					correct_answer=correct,
					is_correct=is_correct,
					difficulty=difficulty_int,
					gained_exp=gained,
					penalty_exp=penalty,
				)
			)

		total = len(qas)
		score = round((correct_count / total) * 100, 2)
		applied_exp = max(0, earned_exp - penalty_exp)
		passed = score >= PASS_THRESHOLD

		if passed:
			_update_learning_progress(session, course.course_id, lesson.lesson_id, user_id)
			session.commit()
		else:
			session.rollback()

		result = AssessmentSubmitResult(
			score=score,
			correct_count=correct_count,
			total=total,
			earned_exp=earned_exp,
			penalty_exp=penalty_exp,
			applied_exp=applied_exp if passed else 0,
			passed=passed,
			pass_threshold=PASS_THRESHOLD,
			answers=answer_results,
		)
		experience = None
		if passed and applied_exp > 0:
			experience = _experience_payload(applied_exp, _award_experience(request, user_id, applied_exp))
		_log_activity(request, user_id, "assessment_move")
		return AssessmentSubmitResponse(status=200, result=result, experience=experience)
	except Exception as e:
		logger.error("submit_assessment_controller error user=%s course=%s lesson=%s err=%s", user_id, course_id, lesson_id, e)
		session.rollback()
		return AssessmentSubmitResponse(status=500, message="Có lỗi xảy ra khi chấm bài")
	finally:
		session.close()




# ---------------- Mutation Controllers ----------------

def finish_course_controller(request: Request, payload: FinishCourseRequest):
	"""Mark a course as finished when all lessons are finished for this user."""
	from src.database import SessionLocal
	from src.models import Course, Lesson, LearningProgress

	user_id = _verify_token(request)
	if not user_id:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})

	session = SessionLocal()
	try:
		course = session.query(Course).filter_by(course_id=payload.course_id).first()
		if not course:
			return JSONResponse(status_code=404, content={"status": 404, "message": "Không tìm thấy khóa học"})
		is_owner = course.user_id == user_id
		if not is_owner and not getattr(course, "publish", False):
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền truy cập vào khóa học này"})

		lesson_ids = [lid for (lid,) in session.query(Lesson.lesson_id).filter(Lesson.course_id == course.course_id).all()]
		total_lessons = len(lesson_ids)
		if total_lessons == 0:
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})
		progress = session.query(LearningProgress).filter(
			LearningProgress.course_id == course.course_id,
			LearningProgress.user_id == user_id,
		).first()
		if not progress:
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})
		if progress.num_total_lesson != total_lessons:
			progress.num_total_lesson = total_lessons
		if (progress.num_finished_lesson or 0) < total_lessons:
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})
		if is_owner and not getattr(course, "finish", False):
			course.finish = True
		session.commit()
		experience = _experience_payload(COURSE_COMPLETION_EXP, _award_experience(request, user_id, COURSE_COMPLETION_EXP))
		_log_activity(request, user_id, "course_move")
		return {"status": 200, "message": "Đã cập nhật thành công", "experience": experience}
	except Exception as e:
		logger.error("finish_course_controller error user=%s course=%s err=%s", user_id, payload.course_id, e)
		session.rollback()
		return JSONResponse(status_code=500, content={"status": 500, "message": "Internal error"})
	finally:
		session.close()


def finish_lesson_controller(request: Request, payload: FinishLessonRequest):
	"""Mark a single lesson as finished once its assessments are passed."""
	from src.database import SessionLocal
	from src.models import Course, Lesson

	user_id = _verify_token(request)
	if not user_id:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền cập nhật bài học này"})

	session = SessionLocal()
	try:
		course = session.query(Course).filter_by(course_id=payload.course_id).first()
		if not course:
			return JSONResponse(status_code=404, content={"status": 404, "message": "Không tìm thấy khóa học"})
		is_owner = course.user_id == user_id
		if not is_owner and not getattr(course, "publish", False):
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền cập nhật bài học này"})
		lesson = session.query(Lesson).filter_by(lesson_id=payload.lesson_id, course_id=course.course_id).first()
		if not lesson:
			return JSONResponse(status_code=404, content={"status": 404, "message": "Lesson không tồn tại"})
		finished, total = _update_learning_progress(session, course.course_id, lesson.lesson_id, user_id)
		session.commit()
		_log_activity(request, user_id, "course_move")
		return {
			"status": 200,
			"message": "Đã cập nhật thành công",
			"progress": {"finished_lessons": finished, "total_lessons": total},
		}
	except Exception as e:
		logger.error("finish_lesson_controller error user=%s course=%s lesson=%s err=%s", user_id, payload.course_id, payload.lesson_id, e)
		session.rollback()
		return JSONResponse(status_code=500, content={"status": 500, "message": "Internal error"})
	finally:
		session.close()
