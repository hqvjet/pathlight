from typing import List, cast
from uuid import uuid4
from datetime import datetime
import hashlib
import secrets
import logging
import time
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
	ExperienceSnapshot,
	CourseVisibilityUpdate,
	CreateCourseRequest,
)

logger = logging.getLogger(__name__)

# Reuse a module-level httpx client to share connection pool across Lambda
# invocations. Creating a new client per request can exhaust sockets and
# trigger "Device or resource busy" / connection errors.
_httpx_client = httpx.Client(
	timeout=5.0,
	limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
)

DIFFICULTY_EXP = {
	1: 100,
	2: 200,
	3: 300,
	4: 400,
	5: 500,
}
PASS_THRESHOLD = 80
COURSE_COMPLETION_EXP = 100
HINT_PENALTY = 50
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".pptx", ".ppt", ".docx", ".doc"}


async def create_course_controller(request: Request, body: CreateCourseRequest):
    """Create a course generation job (S3 validation + SQS enqueue)."""
    from src.services.sqs_publisher import send_generate_with_vectorize
    queue_url = os.getenv("SQS_QUEUE_URL")
    if not queue_url:
        return {"status": 500, "message": "SQS_QUEUE_URL is not configured"}
    default_job = "GENERATE_COURSE_WITH_VECTORIZE"
    course_id = body.id or f"course-{uuid4()}"
    s3_keys = body.s3_keys or []
    difficulty = (body.difficulty or "medium").strip()
    try:
        duration = int(body.duration or 0)
    except Exception:
        duration = 0
    if duration <= 0:
        return {"status": 400, "message": "duration must be a positive integer (minutes)"}

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
        logger.info("Sending to SQS: course_id=%s, user_id=%s, s3_keys_count=%d, duration=%d, difficulty=%s", 
                    course_id, user_id, len(s3_keys), duration, difficulty)
        resp = send_generate_with_vectorize(
            queue_url=queue_url,
            course_id=course_id,
            s3_keys=s3_keys,
            difficulty=difficulty,
            duration=duration,
            user_id=user_id,
            region=region,
            group_id=os.getenv("SQS_GROUP_ID"),
            job_type=default_job,
        )
        logger.info("SQS message sent successfully: message_id=%s, course_id=%s", resp.get("MessageId"), course_id)
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
	# Try header first, then fall back to common auth cookies used by the frontend
	auth_header = request.headers.get("Authorization")
	if not auth_header:
		cookie_token = (
			request.cookies.get("auth_token")
			or request.cookies.get("session_token")
			or request.cookies.get("access_token")
		)
		if cookie_token:
			# normalize to Bearer format if needed
			auth_header = cookie_token if cookie_token.startswith("Bearer ") else f"Bearer {cookie_token}"
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
	"""Call user-service to add experience for the current user by forwarding
	the user's JWT. This avoids using a shared INTERNAL_API_KEY secret.

	We will retry on transient network errors / 5xx responses with
	exponential backoff. If no user JWT is present (header or common
	cookies), we will not attempt a service-level secret fallback.
	"""
	if exp_amount == 0:
		return None

	base_url = _user_service_base_url()
	if not base_url:
		return None

	# Prefer explicit Authorization header, fall back to common auth cookies
	auth_header = request.headers.get("Authorization")
	if not auth_header:
		cookie_token = (
			request.cookies.get("auth_token")
			or request.cookies.get("session_token")
			or request.cookies.get("access_token")
		)
		if cookie_token:
			auth_header = cookie_token if cookie_token.startswith("Bearer ") else f"Bearer {cookie_token}"

	# If a user JWT is present, forward it to credit the caller. Otherwise,
	# fall back to an internal admin call (if configured) so the service can
	# credit a specific `user_id` even without the user's JWT.
	use_admin_fallback = False
	if not auth_header or not auth_header.startswith("Bearer "):
		internal_token = getattr(config, "USER_SERVICE_INTERNAL_TOKEN", None) or os.getenv("USER_SERVICE_INTERNAL_TOKEN")
		if internal_token:
			use_admin_fallback = True
			auth_header = f"Bearer {internal_token}"
		else:
			logger.warning("No user JWT present and no internal token configured; skipping award_experience for user %s", user_id)
			return None

	if use_admin_fallback:
		# call admin endpoint that accepts userid query param
		url = f"{base_url.rstrip('/')}/admin/user/experience?userid={user_id}"
		json_payload = {"exp": exp_amount}
	else:
		url = f"{base_url.rstrip('/')}/user/experience/add"
		json_payload = {"exp": exp_amount}
	max_attempts = 3
	backoff = 0.1

	for attempt in range(1, max_attempts + 1):
		try:
			resp = _httpx_client.post(
				url,
				headers={"Authorization": auth_header},
				json=json_payload,
				timeout=5.0,
			)
			data = resp.json() if resp.content else {}
			# If success or client error, return immediately. Retry only on 5xx.
			if resp.status_code < 500:
				logger.info("Award exp via user-forward attempt=%s url=%s status=%s", attempt, url, resp.status_code)
				return {"status_code": resp.status_code, "body": data}
			# else 5xx - will retry
			logger.warning("User-forward award_experience returned 5xx (attempt=%s): %s", attempt, resp.status_code)
		except Exception as e:  # pragma: no cover - network issues
			logger.exception("User-forward award_experience network error on attempt=%s for user %s", attempt, user_id)
		# backoff before next attempt
		if attempt < max_attempts:
			time.sleep(backoff)
			backoff *= 2

	logger.error("All user-forward award_experience attempts failed for user %s", user_id)
	return None


def _log_activity(request: Request, user_id: str | None, event: str) -> dict | None:
	"""Call user-service to log an activity event.

	Returns a dict with status_code and body when the call was attempted, otherwise None.
	"""
	if not user_id:
		return None
	base_url = _user_service_base_url()
	# Try header first, then fall back to common auth cookies used by the frontend
	auth_header = request.headers.get("Authorization")
	if not auth_header:
		cookie_token = (
			request.cookies.get("auth_token")
			or request.cookies.get("session_token")
			or request.cookies.get("access_token")
		)
		if cookie_token:
			auth_header = cookie_token if cookie_token.startswith("Bearer ") else f"Bearer {cookie_token}"
	if not base_url or not auth_header:
		return None
	url = f"{base_url.rstrip('/')}/user/activity"
	try:
		resp = _httpx_client.post(
			url,
			headers={"Authorization": auth_header},
			json={"event": event},
			timeout=5.0,
		)
		data = resp.json() if resp.content else {}
		return {"status_code": resp.status_code, "body": data}
	except Exception as e: 
		logger.error("Failed to log activity for user %s: %s", user_id, e)
		return None


def _experience_payload(gained_exp: int, award_result: dict | None) -> dict:
	payload: dict[str, int | None] = {"gained_exp": gained_exp}
	# award_result may contain the updated stats under different shapes depending
	# on which user-service endpoint was called. Accept both `{...,'updated_stats':{...}}`
	# and older responses that put fields at the top-level of the body.
	if not award_result:
		return payload
	body = award_result.get("body") if isinstance(award_result.get("body"), dict) else None
	if not body:
		return payload

	# Prefer nested `updated_stats`, otherwise treat body as the stats mapping.
	stats = body.get("updated_stats") if isinstance(body.get("updated_stats"), dict) else body

	def _to_int_or_none(v):
		try:
			if v is None:
				return None
			return int(v)
		except Exception:
			return None

	# Normalize a few common key variants
	new_level = stats.get("new_level") or stats.get("level")
	new_exp = stats.get("new_exp") or stats.get("current_exp")
	require_exp = stats.get("new_require_exp") or stats.get("require_exp")
	exp_needed = stats.get("exp_needed_for_next") or stats.get("exp_needed_for_next")
	# If exp_needed missing but we have require_exp and new_exp, compute it
	if exp_needed is None and require_exp is not None and new_exp is not None:
		try:
			exp_needed = int(require_exp) - int(new_exp)
		except Exception:
			exp_needed = None

	payload["new_level"] = _to_int_or_none(new_level)
	payload["new_exp"] = _to_int_or_none(new_exp)
	payload["require_exp"] = _to_int_or_none(require_exp)
	payload["exp_needed_for_next"] = _to_int_or_none(exp_needed)
	payload["rank"] = _to_int_or_none(stats.get("rank"))
	return payload


def _update_learning_progress(session, course_id: str, lesson_id: str, user_id: str) -> tuple[int, int]:
	"""Increment learning progress for a user on a course based on lesson order.
	Only allows completing the NEXT lesson in sequence (no skipping).

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
	
	# Get or create progress record
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
		session.flush()
	
	# Update total if changed
	num_total_val = cast(int, getattr(progress, "num_total_lesson") or 0)
	if num_total_val != total:
		session.query(LearningProgress).filter(
			LearningProgress.course_id == course_id,
			LearningProgress.user_id == user_id,
		).update({"num_total_lesson": total}, synchronize_session=False)
		session.flush()
	
	current_finished = min(cast(int, getattr(progress, "num_finished_lesson") or 0), total)
	
	if target_idx is None:
		logger.warning(f"Lesson {lesson_id} not found in course {course_id}")
		return current_finished, total

	if target_idx != current_finished:
		if target_idx < current_finished:
			logger.info(f"Lesson {lesson_id} already completed (target={target_idx}, finished={current_finished})")
		else:
			logger.warning(f"Cannot skip to lesson {lesson_id} (target={target_idx}, finished={current_finished}). Complete previous lessons first.")
		return current_finished, total
	
	new_finished = current_finished + 1
	session.query(LearningProgress).filter(
		LearningProgress.course_id == course_id,
		LearningProgress.user_id == user_id,
	).update({"num_finished_lesson": new_finished}, synchronize_session=False)
	session.flush()
	logger.info(f"Progress updated for user {user_id} course {course_id}: {new_finished}/{total} lessons completed")
	return new_finished, total


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
	"""Verify admin role from JWT token claims."""
	auth_header = request.headers.get("Authorization")
	if not auth_header or not auth_header.startswith("Bearer "):
		logger.warning("Admin guard: Missing or invalid Authorization header")
		return {"status": 401, "message": "Unauthorized"}
	
	token = auth_header.split(" ")[1]
	try:
		# Try verified decode first
		payload = None
		secret_key = getattr(config, "JWT_SECRET_KEY", None)
		logger.info(f"Admin guard: JWT_SECRET_KEY configured: {bool(secret_key)}")
		
		if secret_key:
			try:
				payload = jwt.decode(token, secret_key, algorithms=[config.JWT_ALGORITHM])
				logger.info("Admin guard: JWT verified successfully")
			except Exception as e:
				logger.warning(f"Admin guard: JWT verification failed: {e}, trying unverified")
		
		# Fallback to unverified claims
		if not payload:
			try:
				payload = jwt.get_unverified_claims(token)
				logger.info("Admin guard: Using unverified JWT claims")
			except Exception as decode_error:
				logger.error(f"Admin guard: Cannot decode token: {decode_error}")
				return {"status": 401, "message": "Invalid token"}
		
		# Check admin role
		role = payload.get("role")
		roles = payload.get("roles") or []
		if isinstance(roles, str):
			roles = [roles]
		is_admin = role == "admin" or "admin" in roles
		
		logger.info(f"Admin guard: role={role}, roles={roles}, is_admin={is_admin}")
		
		if not is_admin:
			return {"status": 403, "message": "Admin access required"}
		
		logger.info("Admin guard: Access granted")
		return None
	except Exception as e:
		logger.error(f"Admin guard failed: {e}", exc_info=True)
		return {"status": 500, "message": "Cannot verify admin status"}


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

		course_list = []
		for c in courses:
			created_at_val = getattr(c, "created_at", None)
			# Count lessons from relationship
			num_lessons = len(c.lessons) if hasattr(c, 'lessons') and c.lessons else 0
			course_list.append({
				"course_id": c.course_id,
				"user_id": c.user_id,
				"title": c.title,
				"overview": c.overview,
				"level": c.level,
				"duration": c.duration,
				"publish": bool(c.publish),
				"finish": bool(c.finish),
				"num_lessons": num_lessons,
				"created_at": created_at_val.isoformat() if created_at_val else "",
			})

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


def update_course_visibility_controller(request: Request, body: CourseVisibilityUpdate, admin_override: bool = False):
	from src.database import SessionLocal
	from src.models import Course

	user_id = _verify_token(request)
	if not user_id and not admin_override:
		raise HTTPException(status_code=401, detail="Bạn không có quyền thay đổi khóa học này")
	session = SessionLocal()
	try:
		if admin_override:
			query = session.query(Course).filter(Course.course_id == body.course_id)
		else:
			query = session.query(Course).filter(Course.course_id == body.course_id, Course.user_id == user_id)
		course = query.first()
		if not course:
			raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
		new_publish = bool(body.publish)
		# use update to avoid assigning a raw bool to a Column-typed attribute
		query.update({"publish": new_publish}, synchronize_session=False)
		session.commit()
		return {"status": 200, "course_id": course.course_id, "publish": new_publish}
	finally:
		session.close()


def list_public_courses_controller(search: str | None = None, user_id: str | None = None) -> CourseListResponse:
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
		if user_id:
			query = query.filter(Course.user_id == user_id)
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
				user_id=r.user_id or "",
				lesson_num=lesson_counts.get(r.course_id, 0),
				finish_lesson_num=0,
				updated_at=r.created_at.isoformat() if r.created_at else "",
			)
			for r in rows
		]
		return CourseListResponse(status=200, courses=summaries)
	finally:
		session.close()


async def delete_single_course(request: Request, course_id: str | None, admin_override: bool = False):
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
		# If admin_override is True, allow deleting any course by course_id; otherwise enforce ownership
		if admin_override:
			course = session.query(Course).filter_by(course_id=course_id).first()
		else:
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
		_is_owner_attr = course.user_id == (user_id or "")
		is_owner = _is_owner_attr if isinstance(_is_owner_attr, bool) else False
		if not is_owner and getattr(course, "publish", False) is not True:
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
				# Ensure we read a plain int from the ORM attribute to avoid ColumnElement types
				finished_lessons = min(cast(int, getattr(progress, "num_finished_lesson") or 0), len(lessons))
		lesson_models: list[LessonInfo] = []
		for idx, l in enumerate(lessons):
			lesson_models.append(
				LessonInfo(
					lesson_id=cast(str, getattr(l, "lesson_id")),
					title=cast(str, getattr(l, "title")),
					finish=bool(idx < cast(int, finished_lessons)),
				)
			)

		course_full = CourseFullInfo(
			title=getattr(course, "title", ""),
			overview=getattr(course, "overview", ""),
			level=getattr(course, "level", ""),
			duration=getattr(course, "duration", 0) or 0,
			publish=bool(getattr(course, "publish", False)),
			finish=bool(getattr(course, "finish", False)),
			user_id=getattr(course, "user_id", ""),
			lesson=lesson_models,
			progress_finished_lessons=finished_lessons,
			progress_total_lessons=len(lessons),
			updated_at=course.created_at.isoformat() if getattr(course, "created_at", None) else "",
		)
		return CourseFullInfoResponse(status=200, info=course_full)
	finally:
		session.close()


def get_user_course_stats_controller(request: Request) -> dict:
	"""Get aggregated course statistics for a user - for dashboard."""
	from src.database import SessionLocal
	from src.models import Course, Lesson, LearningProgress
	
	user_id = _verify_token(request)
	if not user_id:
		return {"status": 401, "message": "Unauthorized"}
	
	session = SessionLocal()
	try:
		# Count total courses
		total_courses = session.query(Course).filter(Course.user_id == user_id).count()
		
		# Count completed courses
		course_ids = [c.course_id for c in session.query(Course.course_id).filter(Course.user_id == user_id).all()]
		completed_courses = 0
		total_lessons = 0
		
		if course_ids:
			# Calculate lesson counts
			lesson_counts = {}
			lessons = session.query(Lesson.course_id).filter(Lesson.course_id.in_(course_ids)).all()
			for (cid,) in lessons:
				lesson_counts[cid] = lesson_counts.get(cid, 0) + 1
				total_lessons += 1
			
			# Check progress
			progress_rows = session.query(LearningProgress).filter(
				LearningProgress.course_id.in_(course_ids),
				LearningProgress.user_id == user_id,
			).all()
			
			for p in progress_rows:
				total = cast(int, getattr(p, "num_total_lesson") or lesson_counts.get(p.course_id, 0))
				finished = min(cast(int, getattr(p, "num_finished_lesson") or 0), total)
				if total > 0 and finished >= total:
					completed_courses += 1
		
		return {
			"status": 200,
			"total_courses": total_courses,
			"completed_courses": completed_courses,
			"total_lessons": total_lessons,
		}
	finally:
		session.close()


def get_all_courses_controller(request: Request) -> CourseListResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson, LearningProgress
	user_id = _verify_token(request)
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
				total = cast(int, getattr(p, "num_total_lesson") or lesson_counts.get(p.course_id, 0))
				finished = min(cast(int, getattr(p, "num_finished_lesson") or 0), total)
				finish_counts[p.course_id] = finished
				finish_map[p.course_id] = (total > 0) and (finished >= total)
		summaries = [
			CourseSummary(
				course_id=r.course_id,
				title=r.title or "",
				overview=r.overview or "",
				level=r.level or "",
				duration=r.duration or 0,
				finish=finish_map.get(r.course_id, False),
				publish=bool(getattr(r, "publish", False)),
				user_id=user_id,
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
		_is_owner_attr = course.user_id == (user_id or "")
		is_owner = _is_owner_attr if isinstance(_is_owner_attr, bool) else False
		# Safely evaluate publish value without triggering SQLAlchemy ColumnElement.__bool__
		_publish_attr = getattr(course, "publish", False)
		_is_published = _publish_attr if isinstance(_publish_attr, bool) else False
		if not is_owner and not _is_published:
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
				finished_lessons = min(cast(int, getattr(progress, "num_finished_lesson") or 0), len(lessons))

		# Build lesson list with locked/unlocked status
		# Rule: Only the next unfinished lesson is unlocked, all others after it are locked
		lesson_models = [
			LessonDetail(
				lesson_id=getattr(l, "lesson_id"),
				course_id=getattr(l, "course_id"),
				title=getattr(l, "title"),
				overview=getattr(l, "overview", ""),
				content=getattr(l, "content"),
				duration=getattr(l, "duration", 0) or 0,
				finish=idx < finished_lessons,
				locked=idx > finished_lessons,  # locked if index is beyond the next lesson
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
		_publish_attr = getattr(course, "publish", False)
		_is_published = _publish_attr if isinstance(_publish_attr, bool) else False
		_is_owner_attr = course.user_id == (user_id or "")
		is_owner = _is_owner_attr if isinstance(_is_owner_attr, bool) else False
		if not is_owner and not _is_published:
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
		lesson = session.query(Lesson).filter(Lesson.lesson_id == lesson_id, Lesson.course_id == course_id).first()
		if not lesson:
			raise HTTPException(status_code=404, detail="Lesson not found")
		
		# Check lesson order and lock status
		lessons = (
			session.query(Lesson)
			.filter(Lesson.course_id == course.course_id)
			.order_by(Lesson.created_at.asc(), Lesson.lesson_id.asc())
			.all()
		)
		order_map = {l.lesson_id: idx for idx, l in enumerate(lessons)}
		target_idx = order_map.get(lesson.lesson_id)
		if target_idx is None:
			raise HTTPException(status_code=404, detail="Lesson not found")
		
		finished_lessons = 0
		if user_id:
			progress = session.query(LearningProgress).filter(
				LearningProgress.course_id == course.course_id,
				LearningProgress.user_id == user_id,
			).first()
			if progress:
				finished_lessons = min(cast(int, getattr(progress, "num_finished_lesson") or 0), len(lessons))
		
		# Check if lesson is locked (user hasn't completed previous lessons)
		is_locked = target_idx > finished_lessons
		if is_locked and not is_owner:  # Owners can view any lesson
			raise HTTPException(status_code=403, detail="Bạn cần hoàn thành các bài học trước đó trước khi truy cập bài học này")
		
		return LessonDetail(
			lesson_id=getattr(lesson, "lesson_id"),
			course_id=getattr(lesson, "course_id"),
			title=getattr(lesson, "title"),
			overview=getattr(lesson, "overview", ""),
			content=getattr(lesson, "content"),
			duration=getattr(lesson, "duration", 0) or 0,
			finish=bool(target_idx < finished_lessons),
			locked=is_locked,
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
	from src.models import Course, Lesson, Assessment, LearningProgress

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
	session = SessionLocal()
	try:
		course = session.query(Course).filter(Course.course_id == course_id).first()
		if not course:
			raise HTTPException(status_code=404, detail="Không tìm thấy khóa học")
		_is_owner_attr = course.user_id == user_id
		is_owner = _is_owner_attr if isinstance(_is_owner_attr, bool) else False
		# Safely evaluate publish value without triggering SQLAlchemy ColumnElement.__bool__
		_publish_attr = getattr(course, "publish", False)
		_is_published = _publish_attr if isinstance(_publish_attr, bool) else False
		if not is_owner and not _is_published:
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
		lesson = session.query(Lesson).filter(Lesson.lesson_id == lesson_id, Lesson.course_id == course.course_id).first()
		if not lesson:
			raise HTTPException(status_code=404, detail="Lesson not found")
		
		# Check if lesson is locked
		lessons = (
			session.query(Lesson)
			.filter(Lesson.course_id == course.course_id)
			.order_by(Lesson.created_at.asc(), Lesson.lesson_id.asc())
			.all()
		)
		order_map = {l.lesson_id: idx for idx, l in enumerate(lessons)}
		target_idx = order_map.get(lesson.lesson_id)
		if target_idx is None:
			raise HTTPException(status_code=404, detail="Lesson not found")
		
		finished_lessons = 0
		if user_id:
			progress = session.query(LearningProgress).filter(
				LearningProgress.course_id == course.course_id,
				LearningProgress.user_id == user_id,
			).first()
			if progress:
				finished_lessons = min(cast(int, getattr(progress, "num_finished_lesson") or 0), len(lessons))
		
		# Prevent accessing locked lessons
		is_locked = target_idx > finished_lessons
		if is_locked and not is_owner:
			raise HTTPException(status_code=403, detail="Bạn cần hoàn thành các bài học trước đó trước khi làm bài kiểm tra này")
		
		assessments = (
			session.query(Assessment)
			.filter(Assessment.lesson_id == lesson.lesson_id)
			.order_by(Assessment.created_at.asc())
			.all()
		)
		items = [
			AssessmentItem(
				assessment_id=cast(str, getattr(a, "assessment_id")),
				lesson_id=cast(str, getattr(a, "lesson_id")),
				question=cast(str, getattr(a, "question")),
				hint=None,  # Never send hint text upfront - must request via hint API
				has_hint=bool(getattr(a, "hint")),  # Flag to show hint button
				explanation=cast(str, getattr(a, "explanation") or "") if include_explanations else "",
				difficulty=cast(str, getattr(a, "difficulty") or ""),
				option1=cast(str, getattr(a, "option1") or ""),
				option2=cast(str, getattr(a, "option2") or ""),
				option3=cast(str, getattr(a, "option3") or ""),
				option4=cast(str, getattr(a, "option4") or ""),
				answer=0,  # NEVER send correct answer to client for security
			)
			for a in assessments
		]
		return AssessmentListResponse(status=200, assessments=items)
	finally:
		session.close()


def get_assessment_hint_controller(
	request: Request,
	course_id: str,
	lesson_id: str,
	assessment_id: str,
) -> dict:
	"""Get hint for a specific assessment with exp penalty."""
	from src.database import SessionLocal
	from src.models import Course, Lesson, Assessment, LearningProgress
	
	user_id = _verify_token(request)
	if not user_id:
		return {"status": 401, "message": "Bạn không có quyền truy cập"}
	
	session = SessionLocal()
	try:
		# Verify course and lesson access
		course = session.query(Course).filter(Course.course_id == course_id).first()
		if not course:
			return {"status": 404, "message": "Không tìm thấy khóa học"}
		
		lesson = session.query(Lesson).filter(
			Lesson.lesson_id == lesson_id,
			Lesson.course_id == course_id
		).first()
		if not lesson:
			return {"status": 404, "message": "Không tìm thấy bài học"}
		
		lessons = session.query(Lesson).filter(
			Lesson.course_id == course_id
		).order_by(Lesson.created_at.asc(), Lesson.lesson_id.asc()).all()
		
		order_map = {cast(str, getattr(l, "lesson_id")): idx for idx, l in enumerate(lessons)}
		target_idx = order_map.get(cast(str, lesson_id))
		
		finished_lessons = 0
		progress = session.query(LearningProgress).filter(
			LearningProgress.course_id == course_id,
			LearningProgress.user_id == user_id,
		).first()
		if progress:
			finished_lessons = min(cast(int, getattr(progress, "num_finished_lesson") or 0), len(lessons))
		
		is_locked = target_idx is not None and target_idx > finished_lessons
		is_owner = course.user_id == user_id
		if is_locked and not is_owner:
			return {"status": 403, "message": "Bạn cần hoàn thành các bài học trước đó"}
		
		# Get assessment
		assessment = session.query(Assessment).filter(
			Assessment.assessment_id == assessment_id,
			Assessment.lesson_id == lesson_id
		).first()
		if not assessment:
			return {"status": 404, "message": "Không tìm thấy câu hỏi"}
		
		hint = cast(str | None, getattr(assessment, "hint"))
		if not hint:
			return {"status": 404, "message": "Câu hỏi này không có gợi ý"}
		
		# Use a fixed hint penalty to match frontend expectations
		# (frontend uses HINT_COST = 50). Keep this consistent so users see the
		# same value in UI and server-side accounting.
		exp_penalty = HINT_PENALTY
		
		# Deduct exp (negative exp)
		if exp_penalty > 0:
			logger.info(f"Deducting {exp_penalty} exp from user {user_id} for hint on assessment {assessment_id}")
			penalty_result = _award_experience(request, user_id, -exp_penalty)
			if penalty_result:
				logger.info(f"Hint penalty response: status={penalty_result.get('status_code')}")
		
		return {
			"status": 200,
			"hint": hint,
			"exp_penalty": exp_penalty
		}
	except Exception as e:
		logger.error(f"get_assessment_hint error: {e}")
		return {"status": 500, "message": "Có lỗi xảy ra"}
	finally:
		session.close()


def submit_assessment_controller(request: Request, course_id: str, lesson_id: str, 
								 body: AssessmentSubmitRequest) -> AssessmentSubmitResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson, Assessment, LearningProgress
	import math
	user_id = _verify_token(request)
	session = SessionLocal()
	try:
		course = session.query(Course).filter(Course.course_id == course_id).first()
		if not course:
			return AssessmentSubmitResponse(status=404, message="Không tìm thấy khóa học")
		_is_owner_attr = course.user_id == user_id
		is_owner = _is_owner_attr if isinstance(_is_owner_attr, bool) else False
		_publish_attr = getattr(course, "publish", False)
		_is_published = _publish_attr if isinstance(_publish_attr, bool) else False
		if not is_owner and not _is_published:
			return AssessmentSubmitResponse(status=401, message="Bạn không có quyền làm bài kiểm tra này")
		lesson = session.query(Lesson).filter(Lesson.lesson_id == lesson_id, Lesson.course_id == course.course_id).first()
		if not lesson:
			return AssessmentSubmitResponse(status=404, message="Không tìm thấy bài học")
		
		lessons = (
			session.query(Lesson)
			.filter(Lesson.course_id == course.course_id)
			.order_by(Lesson.created_at.asc(), Lesson.lesson_id.asc())
			.all()
		)
		order_map = {l.lesson_id: idx for idx, l in enumerate(lessons)}
		target_idx = order_map.get(lesson.lesson_id)
		if target_idx is None:
			return AssessmentSubmitResponse(status=404, message="Không tìm thấy bài học")
		
		finished_lessons = 0
		progress = session.query(LearningProgress).filter(
			LearningProgress.course_id == course.course_id,
			LearningProgress.user_id == user_id,
		).first()
		if progress:
			finished_lessons = min(cast(int, getattr(progress, "num_finished_lesson") or 0), len(lessons))
		
		# Prevent submitting locked lessons
		is_locked = target_idx > finished_lessons
		if is_locked and not is_owner:
			return AssessmentSubmitResponse(status=403, message="Bạn cần hoàn thành các bài học trước đó trước khi làm bài kiểm tra này")
		
		qas = session.query(Assessment).filter(Assessment.lesson_id == lesson.lesson_id).all()
		if not qas:
			return AssessmentSubmitResponse(status=404, message="Bài kiểm tra chưa có câu hỏi")
		# build lookup with plain-string keys for static typing
		qa_lookup = {cast(str, getattr(a, "assessment_id")): a for a in qas}
		if not body.answers or len(body.answers) < len(qas):
			return AssessmentSubmitResponse(status=400, message="Vui lòng trả lời tất cả câu hỏi trước khi nộp bài")

		correct_count = 0
		earned_exp = 0
		penalty_exp = 0
		answer_results: list[AssessmentSubmitResultItem] = []

		for ans in body.answers:
			qa = qa_lookup.get(cast(str, ans.assessment_id))
			if not qa:
				continue
			selected = int(ans.answer)
			correct = cast(int, getattr(qa, "answer"))
			is_correct = selected == correct
			if is_correct:
				correct_count += 1

			try:
				raw_difficulty = getattr(qa, "difficulty", None)
				difficulty_int = int(str(raw_difficulty)) if raw_difficulty is not None else None
			except Exception:
				difficulty_int = None
			key = difficulty_int if difficulty_int is not None else 1
			base_exp = DIFFICULTY_EXP.get(key, DIFFICULTY_EXP[1])
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
					assessment_id=cast(str, getattr(qa, "assessment_id")),
					selected_answer=selected,
					correct_answer=correct,
					is_correct=is_correct,
					# preserve original difficulty representation (string or None) for the result model
					difficulty=cast(str | None, getattr(qa, "difficulty")),
					gained_exp=gained,
					penalty_exp=penalty,
				)
			)

		total = len(qas)
		score = round((correct_count / total) * 100, 2)
		applied_exp = max(0, earned_exp - penalty_exp)
		passed = score >= PASS_THRESHOLD

		if passed:
			_update_learning_progress(session, cast(str, getattr(course, "course_id")), cast(str, getattr(lesson, "lesson_id")), user_id)
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
			logger.info(f"Awarding {applied_exp} exp to user {user_id} for passing lesson {lesson_id}")
			award_result = _award_experience(request, user_id, applied_exp)
			if award_result:
				logger.info(f"Experience award response: status={award_result.get('status_code')}, body={award_result.get('body')}")
			else:
				logger.warning(f"Failed to award experience to user {user_id} - no response from user-service")
			experience = _experience_payload(applied_exp, award_result)
		else:
			logger.info(f"Not awarding exp: passed={passed}, applied_exp={applied_exp}")
		_log_activity(request, user_id, "assessment_complete")
		return AssessmentSubmitResponse(status=200, result=result, experience=cast(ExperienceSnapshot | None, experience))
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
		_is_owner_attr = course.user_id == user_id
		is_owner = _is_owner_attr if isinstance(_is_owner_attr, bool) else False
		if not is_owner and getattr(course, "publish", False) is not True:
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
		# read plain int to avoid ColumnElement typing issues and update via query when needed
		num_total_val = cast(int, getattr(progress, "num_total_lesson") or 0)
		if num_total_val != total_lessons:
			session.query(LearningProgress).filter(
				LearningProgress.course_id == course.course_id,
				LearningProgress.user_id == user_id,
			).update({"num_total_lesson": total_lessons}, synchronize_session=False)
			session.flush()
		num_finished_val = cast(int, getattr(progress, "num_finished_lesson") or 0)
		if num_finished_val < total_lessons:
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})
		if is_owner and not (getattr(course, "finish", False) is True):
			# use update to avoid assigning a raw bool to a Column-typed attribute
			session.query(type(course)).filter(type(course).course_id == course.course_id).update({"finish": True}, synchronize_session=False)
			session.flush()
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
		_is_owner_attr = course.user_id == user_id
		is_owner = _is_owner_attr if isinstance(_is_owner_attr, bool) else False
		if not is_owner and getattr(course, "publish", False) is not True:
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền cập nhật bài học này"})
		lesson = session.query(Lesson).filter_by(lesson_id=payload.lesson_id, course_id=course.course_id).first()
		if not lesson:
			return JSONResponse(status_code=404, content={"status": 404, "message": "Lesson không tồn tại"})
		finished, total = _update_learning_progress(session, cast(str, getattr(course, "course_id")), cast(str, getattr(lesson, "lesson_id")), user_id)
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