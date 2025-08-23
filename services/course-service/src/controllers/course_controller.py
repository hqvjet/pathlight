from typing import List, Dict, Any
from datetime import datetime
import hashlib
import uuid
import secrets
import logging

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse
from jose import jwt

from src.config import config
from src.database import SessionLocal
from src.models import Course, CourseInfo, UnderstandLevelTag
import httpx

logger = logging.getLogger(__name__)


def _verify_token(request: Request):
	"""Return user_id (sub) if Authorization header is valid; otherwise None."""
	try:
		auth_header = request.headers.get("Authorization")
		if not auth_header or not auth_header.startswith("Bearer "):
			return None
		token = auth_header.split(" ")[1]
		payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
		return payload.get("sub")
	except Exception:
		return None


def _get_s3_client():
	"""Create S3 client supporting both AWS cloud and S3-compatible endpoints."""
	kwargs = {
		"service_name": "s3",
		"aws_access_key_id": getattr(config, "ACCESS_KEY_ID", None) or None,
		"aws_secret_access_key": getattr(config, "SECRET_ACCESS_KEY", None) or None,
		"region_name": getattr(config, "REGION", None) or None,
	}
	return boto3.client(**kwargs)


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
	user_id = _verify_token(request)
	if not user_id:
		logger.warning("Upload aborted: unauthorized (missing/invalid bearer token)")
		return JSONResponse(status_code=401, content={"status": 401, "message": "Unauthorized"})

	allowed_ext = {".pdf", ".pptx", ".docx", ".doc"}
	total_size = 0
	file_payloads = []
	for f in files:
		original = f.filename or ""
		ext = "." + original.rsplit(".", 1)[1].lower() if "." in original else ""
		if ext not in allowed_ext:
			logger.warning("Upload failed: unsupported extension '%s' for file '%s' (user_id=%s)", ext, original, user_id)
			return {"status": 401, "message": "Định dạng file không được hỗ trợ"}
		content = await f.read()
		total_size += len(content)
		if total_size > 20 * 1024 * 1024:
			logger.warning("Upload failed: total size %d exceeds 20MB limit (user_id=%s)", total_size, user_id)
			return {"status": 401, "message": "File vượt quá dung lượng giới hạn, xin vui lòng xem lại"}
		enc_name = _encrypted_filename(user_id, original)
		file_payloads.append((f, content, enc_name))

	s3 = _get_s3_client()
	bucket = config.S3_BUCKET_NAME
	if not bucket:
		logger.error("Upload failed: S3_BUCKET_NAME is not configured")
		return {"status": 500, "message": "S3_BUCKET_NAME is not configured"}

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
		key = enc_name
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


async def create_course(request: Request, payload: Dict[str, Any]):
	status, token, user_id = _auth_and_decode(request)
	if status is not None:
		return status
	assert token is not None and user_id is not None, "Auth decode should guarantee token & user_id"
	token_str: str = token
	user_id_str: str = user_id

	valid, err_resp, fields = _validate_create_course_payload(payload)
	if not valid:
		return err_resp
	(title, description, understand_level, duration, uploaded_files) = fields  # type: ignore

	course_id = str(uuid.uuid4())
	course_info_id = str(uuid.uuid4())

	v_ok = await _call_vectorize(course_id, uploaded_files, token_str)
	if not v_ok:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Có lỗi xảy ra, xin vui lòng thử lại"})
	g_ok = await _call_generate(course_id, understand_level, duration, token_str)
	if not g_ok:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Có lỗi xảy ra, xin vui lòng thử lại"})

	persist_ok = _persist_course(course_id, course_info_id, user_id_str, title, description, understand_level, duration)
	if not persist_ok:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Có lỗi xảy ra, xin vui lòng thử lại"})

	return JSONResponse(status_code=200, content={"status": 200, "message": "Đã tạo khóa học thành công"})

def _auth_and_decode(request: Request):
	auth_header = request.headers.get("Authorization") or ""
	if not auth_header.startswith("Bearer "):
		return JSONResponse(status_code=401, content={"status": 401, "message": "Unauthorized"}), None, None
	token = auth_header.split(" ", 1)[1]
	try:
		decoded = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
		user_id = decoded.get("sub")
		if not user_id:
			return JSONResponse(status_code=401, content={"status": 401, "message": "Unauthorized"}), None, None
		return None, token, user_id
	except Exception:
		logger.info("create_course invalid token decode")
		return JSONResponse(status_code=401, content={"status": 401, "message": "Unauthorized"}), None, None


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


async def _call_vectorize(course_id: str, uploaded_files: List[str], token: str) -> bool:
	vectorize_url = f"{config.AGENTIC_SERVICE_ENDPOINT}"
	payload = {"id": course_id, "category": 0, "uploaded_file": uploaded_files}
	return await _post_agentic(vectorize_url, payload, token, phase="vectorize")


async def _call_generate(course_id: str, understand_level: str, duration_hours: int, token: str) -> bool:
	generate_url = f"{config.AGENTIC_SERVICE_ENDPOINT}"
	payload = {"id": course_id, "difficulty": understand_level, "duration": duration_hours * 60}
	return await _post_agentic(generate_url, payload, token, phase="generate")

async def _post_agentic(url: str, payload: Dict[str, Any], token: str, phase: str) -> bool:
	"""Post to agentic endpoint supporting two modes:
	1. Default (no SigV4 required): send token in X-User-Token header (avoid Authorization clash with AWS IAM)
	2. SigV4 mode (if AGENTIC_EXPECT_SIGV4=true): sign request and optionally include token as X-User-Token.
	"""
	import os, json as _json
	use_sigv4 = str(os.getenv("AGENTIC_EXPECT_SIGV4", "")).lower() in {"1", "true", "yes"}
	headers = {"Content-Type": "application/json"}
	# Always pass user token in a neutral header to avoid AWS parser rejecting plain bearer
	headers["X-User-Token"] = token
	body = _json.dumps(payload)
	if use_sigv4:
		try:
			from botocore.auth import SigV4Auth  # type: ignore
			from botocore.awsrequest import AWSRequest  # type: ignore
			from botocore.credentials import Credentials  # type: ignore
			region = os.getenv("REGION", getattr(config, "REGION", "ap-northeast-1"))
			creds = Credentials(os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"], os.getenv("AWS_SESSION_TOKEN"))
			aws_req = AWSRequest(method="POST", url=url, data=body, headers={"Content-Type": "application/json"})
			SigV4Auth(creds, "lambda", region).add_auth(aws_req)
			# Merge signed headers
			for k, v in aws_req.headers.items():
				headers[k] = v
		except Exception as e:
			logger.error("%s signing error: %s", phase, e)
			return False
	try:
		async with httpx.AsyncClient(timeout=120) as client:
			resp = await client.post(url, content=body, headers=headers)
	except Exception as e:
		logger.error("%s request error: %s", phase, e)
		return False
	if resp.status_code != 200:
		logger.error("%s failed status=%s body=%s", phase, resp.status_code, resp.text)
		return False
	return True


def _persist_course(course_id: str, course_info_id: str, user_id: str, title: str, description: str, understand_level: str, duration: int) -> bool:
	# Allow tests / certain environments to skip DB persistence entirely
	import os
	if str(os.getenv("COURSE_SERVICE_SKIP_DB", "")).lower() in {"1", "true", "yes"}:
		logger.info("Skipping DB persistence (COURSE_SERVICE_SKIP_DB set) user=%s course_id=%s", user_id, course_id)
		return True

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

		course_info = CourseInfo(
			course_info_id=course_info_id,
			understand_level_id=level.understand_level_id,
			title=title,
			description=description,
			duration=duration,
			roadmap=None,
		)
		course = Course(
			course_id=course_id,
			course_info_id=course_info.course_info_id,
			user_id=user_id,
			finish=False,
		)
		session.add(course_info)
		session.add(course)
		session.commit()
		logger.info("create_course success user=%s course_id=%s", user_id, course_id)
		return True
	except Exception as e:
		session.rollback()
		logger.error("DB save failed course_id=%s error=%s", course_id, e)
		return False
	finally:
		session.close()
