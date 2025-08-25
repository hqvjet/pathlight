from typing import List
from datetime import datetime
import hashlib
import secrets
import logging

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse
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



def _unauth_delete_response():
	return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa xác thực hoặc phiên đăng nhập đã hết hạn"})


async def delete_single_course(request: Request, course_id: str | None):
	"""Delete one course of the authenticated user (and its related data)."""
	user_id = _verify_token(request)
	if not user_id:
		return _unauth_delete_response()
	if not course_id:
		return _unauth_delete_response()
	from src.database import SessionLocal
	from src.models import Course, Lesson, Test, LessonQA, FinalTest, FinalQA, CourseInfo
	session = SessionLocal()
	try:
		course = session.query(Course).filter_by(course_id=course_id, user_id=user_id).first()
		if not course:
			return _unauth_delete_response()
		lesson_ids = [l.lesson_id for l in session.query(Lesson.lesson_id).filter(Lesson.course_id == course.course_id).all()]
		test_ids = [t.test_id for t in session.query(Test.test_id).filter(Test.lesson_id.in_(lesson_ids)).all()] if lesson_ids else []
		final_test_ids = [ft.final_test_id for ft in session.query(FinalTest.final_test_id).filter(FinalTest.course_id == course.course_id).all()]
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
		course_info_id = course.course_info_id
		session.delete(course)
		other = session.query(Course).filter(Course.course_info_id == course_info_id).first()
		if not other:
			session.query(CourseInfo).filter(CourseInfo.course_info_id == course_info_id).delete(synchronize_session=False)
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
	from src.database import SessionLocal
	from src.models import Course, Lesson, Test, LessonQA, FinalTest, FinalQA, CourseInfo
	session = SessionLocal()
	try:
		courses = session.query(Course).filter(Course.user_id == user_id).all()
		if not courses:
			return JSONResponse(status_code=200, content={"status": 200, "message": "Đã xóa toàn bộ khóa học thành công"})
		course_ids = [c.course_id for c in courses]
		course_info_ids = [c.course_info_id for c in courses]
		lesson_ids = [lid for (lid,) in session.query(Lesson.lesson_id).filter(Lesson.course_id.in_(course_ids)).all()]
		test_ids = [tid for (tid,) in session.query(Test.test_id).filter(Test.lesson_id.in_(lesson_ids)).all()] if lesson_ids else []
		final_test_ids = [fid for (fid,) in session.query(FinalTest.final_test_id).filter(FinalTest.course_id.in_(course_ids)).all()]
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
		session.query(Course).filter(Course.course_id.in_(course_ids), Course.user_id == user_id).delete(synchronize_session=False)
		for ci in course_info_ids:
			still = session.query(Course).filter(Course.course_info_id == ci).first()
			if not still:
				session.query(CourseInfo).filter(CourseInfo.course_info_id == ci).delete(synchronize_session=False)
		session.commit()
		return JSONResponse(status_code=200, content={"status": 200, "message": "Đã xóa toàn bộ khóa học thành công"})
	except Exception as e:
		logger.error("delete_all_courses error user=%s err=%s", user_id, e)
		session.rollback()
		return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền xóa khóa học của người khác"})
	finally:
		session.close()
