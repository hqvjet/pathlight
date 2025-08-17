from typing import List
from datetime import datetime
import hashlib
import secrets
import logging

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from fastapi import Request, UploadFile
from jose import jwt

from src.config import config

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
	"""Create S3 client supporting both AWS cloud and local S3-compatible endpoints."""
	kwargs = {
		"service_name": "s3",
		"aws_access_key_id": config.AWS_ACCESS_KEY_ID or None,
		"aws_secret_access_key": config.AWS_SECRET_ACCESS_KEY or None,
		"region_name": config.AWS_REGION or None,
		"config": BotoConfig(s3={"addressing_style": "path"} if config.S3_FORCE_PATH_STYLE else {}),
	}
	if config.AWS_S3_ENDPOINT_URL:
		kwargs["endpoint_url"] = config.AWS_S3_ENDPOINT_URL
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
		return {"status": 401, "message": "Unauthorized"}

	allowed_ext = {".pdf", ".pptx", ".docx"}
	total_size = 0
	file_payloads = []
	for f in files:
		original = f.filename or ""
		ext = "." + original.rsplit(".", 1)[1].lower() if "." in original else ""
		if ext not in allowed_ext:
			return {"status": 401, "message": "Định dạng file không được hỗ trợ"}
		content = await f.read()
		total_size += len(content)
		if total_size > 20 * 1024 * 1024:
			return {"status": 401, "message": "File vượt quá dung lượng giới hạn, xin vui lòng xem lại"}
		enc_name = _encrypted_filename(user_id, original)
		file_payloads.append((f, content, enc_name))

	s3 = _get_s3_client()
	bucket = config.S3_BUCKET_NAME
	if not bucket:
		return {"status": 500, "message": "S3_BUCKET_NAME is not configured"}

	prefix = config.S3_UPLOAD_PREFIX.strip("/")

	# Optional quick bucket check for clearer errors
	try:
		s3.head_bucket(Bucket=bucket)
	except EndpointConnectionError as e:
		logger.error("S3 endpoint connection failed: %s", str(e))
		return {"status": 500, "message": "Cannot connect to S3 endpoint. Check AWS_S3_ENDPOINT_URL and network."}
	except NoCredentialsError:
		logger.error("AWS credentials not found")
		return {"status": 500, "message": "AWS credentials missing. Configure AWS_ACCESS_KEY_ID/SECRET."}
	except ClientError as e:
		code = e.response.get("Error", {}).get("Code", "ClientError")
		logger.error("S3 head_bucket error: %s", code)
		# Common cases: 403 Forbidden (no access), 404 Not Found (bucket missing)
		if code in {"403", "Forbidden"}:
			return {"status": 500, "message": "Access denied to S3 bucket. Check IAM permissions."}
		if code in {"404", "NotFound", "NoSuchBucket"}:
			return {"status": 500, "message": "S3 bucket not found. Ensure bucket exists in the configured region."}
		if code in {"301", "PermanentRedirect", "AuthorizationHeaderMalformed"}:
			return {"status": 500, "message": "S3 region mismatch. Verify AWS_REGION matches the bucket's region."}
		return {"status": 500, "message": f"S3 error: {code}"}

	uploaded_names = []
	for f, body, enc_name in file_payloads:
		key = f"{prefix}/{user_id}/{enc_name}" if prefix else f"{user_id}/{enc_name}"
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
			return {"status": 500, "message": "AWS credentials missing during upload."}
		except ClientError as e:
			code = e.response.get("Error", {}).get("Code", "ClientError")
			logger.error("S3 put_object error: %s", code)
			if code in {"301", "PermanentRedirect", "AuthorizationHeaderMalformed"}:
				return {"status": 500, "message": "S3 region mismatch during upload. Verify AWS_REGION and bucket region."}
			return {"status": 500, "message": f"S3 upload failed: {code}"}

	return {"status": 200, "uploaded_file": uploaded_names}
