"""Course controller (gọn nhẹ)"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib, uuid, secrets, logging, os

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse
from jose import jwt
import httpx

from src.config import config
SessionLocal = None  # type: ignore
Course = CourseInfo = UnderstandLevelTag = None  # type: ignore

def _lazy_models():
	global SessionLocal, Course, CourseInfo, UnderstandLevelTag
	if SessionLocal is None:
		from src.database import SessionLocal as _SL  # type: ignore
		from src.models import Course as _C, CourseInfo as _CI, UnderstandLevelTag as _UL  # type: ignore
		SessionLocal, Course, CourseInfo, UnderstandLevelTag = _SL, _C, _CI, _UL
	return SessionLocal, Course, CourseInfo, UnderstandLevelTag

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _decode(request: Request) -> Tuple[Optional[str], Optional[str]]:
	auth = request.headers.get("Authorization", "")
	if not auth.startswith("Bearer "):
		return None, None
	token = auth.split(" ", 1)[1]
	try:
		payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
		return payload.get("sub"), token
	except Exception:
		return None, None


def _get_s3_client():
	return boto3.client(
		"s3",
		aws_access_key_id=getattr(config, "ACCESS_KEY_ID", None) or None,
		aws_secret_access_key=getattr(config, "SECRET_ACCESS_KEY", None) or None,
		region_name=getattr(config, "REGION", None) or None,
	)


def _encrypted_filename(user_id: str, original_name: str) -> str:
	ext = ""
	if "." in original_name:
		ext = "." + original_name.rsplit(".", 1)[1].lower()
	salt = secrets.token_hex(8)
	seed = f"{user_id}|{original_name}|{datetime.utcnow().isoformat()}|{salt}"
	digest = hashlib.sha256(seed.encode()).hexdigest()
	numeric = str(int(digest, 16) % 10**12).zfill(12)
	return f"{numeric}{ext}"


async def upload_files_docs(request: Request, files: List[UploadFile]):
	user_id, _ = _decode(request)
	if not user_id:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Unauthorized"})

	allowed = {".pdf", ".pptx", ".docx", ".doc"}
	total = 0
	staged: List[Tuple[UploadFile, bytes, str]] = []
	for f in files:
		name = f.filename or ""
		ext = "." + name.rsplit(".", 1)[1].lower() if "." in name else ""
		if ext not in allowed:
			return {"status": 401, "message": "Định dạng file không được hỗ trợ"}
		body = await f.read()
		total += len(body)
		if total > 20 * 1024 * 1024:
			return {"status": 401, "message": "File vượt quá dung lượng giới hạn, xin vui lòng xem lại"}
		staged.append((f, body, _encrypted_filename(user_id, name)))

	bucket = config.S3_BUCKET_NAME
	if not bucket:
		return {"status": 500, "message": "S3_BUCKET_NAME is not configured"}

	s3 = _get_s3_client()
	try:
		s3.head_bucket(Bucket=bucket)
	except (EndpointConnectionError, NoCredentialsError, ClientError) as e:
		return _s3_error(e)

	uploaded: List[str] = []
	for f, body, key in staged:
		try:
			s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType=f.content_type or "application/octet-stream")
			uploaded.append(key)
		except (EndpointConnectionError, NoCredentialsError, ClientError) as e:
			return _s3_error(e)
	return {"status": 200, "uploaded_file": uploaded}


async def create_course(request: Request, payload: Dict[str, Any]):
	user_id, token = _decode(request)
	if not user_id or not token:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Unauthorized"})

	valid, err_resp, fields = _validate_create_course_payload(payload)
	if not valid:
		return err_resp
	title, description, understand_level, duration, uploaded_files = fields  # type: ignore

	course_id, course_info_id = str(uuid.uuid4()), str(uuid.uuid4())
	ok_v, err_v = await _call_vectorize(course_id, uploaded_files, token)
	if not ok_v:
		return _error_response("vectorize", err_v)
	ok_g, err_g = await _call_generate(course_id, understand_level, duration, token)
	if not ok_g:
		return _error_response("generate", err_g)
	if not _persist_course(course_id, course_info_id, user_id, title, description, understand_level, duration):
		return _error_response("persist", "db_persist_failed")
	return JSONResponse(status_code=200, content={"status": 200, "message": "Đã tạo khóa học thành công"})


def _validate_create_course_payload(payload: Dict[str, Any]):
	title = payload.get("title")
	description = payload.get("description")
	understand_level = payload.get("understand_level")
	duration = payload.get("duration")
	uploaded_files = payload.get("uploaded_file")
	if not uploaded_files or not isinstance(uploaded_files, list):
		return False, JSONResponse(status_code=401, content={"status": 401, "message": "Không tìm thấy file, xin vui lòng thử lại"}), None
	if not title or not description or not understand_level or not duration:
		return False, JSONResponse(status_code=401, content={"status": 401, "message": "Không tìm thấy file, xin vui lòng thử lại"}), None
	return True, None, (title, description, understand_level, duration, uploaded_files)


async def _call_vectorize(course_id: str, uploaded_files: List[str], token: str) -> Tuple[bool, Optional[str]]:
	vectorize_url = f"{config.AGENTIC_SERVICE_ENDPOINT}"
	payload = {"id": course_id, "category": 0, "uploaded_file": uploaded_files}
	return await _post_agentic(vectorize_url, payload, token, phase="vectorize")


async def _call_generate(course_id: str, understand_level: str, duration_hours: int, token: str) -> Tuple[bool, Optional[str]]:
	generate_url = f"{config.AGENTIC_SERVICE_ENDPOINT}"
	payload = {"id": course_id, "difficulty": understand_level, "duration": duration_hours * 60}
	return await _post_agentic(generate_url, payload, token, phase="generate")

async def _post_agentic(url: str, payload: Dict[str, Any], token: str, phase: str) -> Tuple[bool, Optional[str]]:
	use_sigv4 = str(os.getenv("AGENTIC_EXPECT_SIGV4", "")).lower() in {"1", "true", "yes"}
	default_timeout = 60 if phase == "vectorize" else 120
	try:
		timeout = int(os.getenv("COURSE_AGENTIC_TIMEOUT_SECONDS", "") or default_timeout)
	except ValueError:
		timeout = default_timeout
	body = __import__("json").dumps(payload)
	headers = {"Content-Type": "application/json", "X-User-Token": token}
	if use_sigv4:
		try:
			from botocore.auth import SigV4Auth
			from botocore.awsrequest import AWSRequest
			from botocore.credentials import Credentials
			region = os.getenv("REGION", getattr(config, "REGION", "ap-northeast-1"))
			creds = Credentials(os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"], os.getenv("AWS_SESSION_TOKEN"))
			aws_req = AWSRequest(method="POST", url=url, data=body, headers={"Content-Type": "application/json"})
			SigV4Auth(creds, "lambda", region).add_auth(aws_req)
			headers.update(dict(aws_req.headers))
		except Exception as e:
			return False, str(e)
	try:
		async with httpx.AsyncClient(timeout=timeout) as client:
			resp = await client.post(url, content=body, headers=headers)
	except httpx.TimeoutException:
		return False, f"timeout after {timeout}s"
	except Exception as e:
		return False, str(e)
	if resp.status_code != 200:
		return False, f"status={resp.status_code} body={resp.text[:400]}"
	return True, None

def _error_response(phase: str, backend_error: Optional[str]):
	verbose = str(os.getenv("COURSE_VERBOSE_ERRORS", "")).lower() in {"1", "true", "yes"} or bool(os.getenv("DEBUG"))
	if backend_error and verbose:
		return JSONResponse(status_code=500, content={"status": 500, "message": f"{phase} failed", "detail": backend_error})
	return JSONResponse(status_code=401, content={"status": 401, "message": "Có lỗi xảy ra, xin vui lòng thử lại"})


def _persist_course(course_id: str, course_info_id: str, user_id: str, title: str, description: str, understand_level: str, duration: int) -> bool:
	if str(os.getenv("COURSE_SERVICE_SKIP_DB", "")).lower() in {"1", "true", "yes"}:
		return True
	_SL, _C, _CI, _UL = _lazy_models()
	session = _SL()
	try:
		level = session.query(_UL).filter_by(understand_level=understand_level).first()
		if not level:
			level = _UL(understand_level_id=str(uuid.uuid4()), understand_level=understand_level)
			session.add(level)
			session.flush()
		info = _CI(
			course_info_id=course_info_id,
			understand_level_id=level.understand_level_id,
			title=title,
			description=description,
			duration=duration,
			roadmap=None,
		)
		course = _C(course_id=course_id, course_info_id=info.course_info_id, user_id=user_id, finish=False)
		session.add(info)
		session.add(course)
		session.commit()
		return True
	except Exception:
		session.rollback()
		return False
	finally:
		session.close()


def _s3_error(exc: Exception):
	if isinstance(exc, EndpointConnectionError):
		return {"status": 500, "message": "Cannot connect to S3 endpoint."}
	if isinstance(exc, NoCredentialsError):
		return {"status": 500, "message": "Credentials missing."}
	if isinstance(exc, ClientError):
		code = exc.response.get("Error", {}).get("Code", "")
		if code in {"NoSuchBucket", "404", "NotFound"}:
			return {"status": 500, "message": "S3 bucket not found."}
		if code in {"403", "Forbidden"}:
			return {"status": 500, "message": "Access denied to S3 bucket."}
		if code in {"301", "PermanentRedirect", "AuthorizationHeaderMalformed"}:
			return {"status": 500, "message": "S3 region mismatch."}
		return {"status": 500, "message": f"S3 error: {code or 'unknown'}"}
	return {"status": 500, "message": "S3 error"}
