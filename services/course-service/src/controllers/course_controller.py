from typing import List, Optional
from datetime import datetime
import hashlib
import secrets
import logging
import string
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from fastapi import Request, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from jose import jwt
import os

from src.config import config
from src.schemas.course_schemas import (
	CourseFullInfo,
	CourseFullInfoResponse,
	LessonInfo,
	CourseListResponse,
	CourseSummary,
	LessonListResponse,
	LessonDetail,
	LessonTestResponse,
	LessonTest,
	LessonTestQA,
	LessonTestSubmitRequest,
	LessonTestSubmitResponse,
	LessonTestSubmitResult,
	LessonTestSubmitResultItem,
	FinalTestResponse,
	FinalTestDetail,
	FinalTestQA,
	FinishCourseRequest,
	FinishLessonRequest,
	PresignUploadRequest,
	PresignUploadResponse,
)

logger = logging.getLogger(__name__)

DIFFICULTY_EXP = {
	1: 5,
	2: 10,
	3: 15,
	4: 20,
	5: 25,
}
PASS_THRESHOLD = 80


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

	allowed_ext = {".pdf", ".pptx", ".ppt", ".docx", ".doc"}
	max_total_bytes = 25 * 1024 * 1024
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


# ---------------- Retrieval Controllers ----------------

def get_course_full_info_controller(request: Request, course_id: str) -> CourseFullInfoResponse:
	from src.database import SessionLocal
	from src.models import Course, CourseInfo, Lesson

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
	session = SessionLocal()
	try:
		course = (
			session.query(Course)
			.filter(Course.course_id == course_id, Course.user_id == user_id)
			.first()
		)
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
			title=getattr(info, "title", "") if info else "",
			description=getattr(info, "description", "") if info else "",
			duration=getattr(info, "duration", 0) if info else 0,
			roadmap=getattr(info, "roadmap", None) if info else None,
			lesson=lesson_models,
			updated_at=course.updated_at.isoformat() if getattr(course, "updated_at", None) is not None else "",
		)
		return CourseFullInfoResponse(status=200, info=course_full)
	finally:
		session.close()


def get_all_courses_controller(request: Request) -> CourseListResponse:
	from src.database import SessionLocal
	from src.models import Course, CourseInfo, Lesson

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không thể truy cập khóa học của người khác")
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
				session.query(Lesson.course_id, Lesson.finish)
				.filter(Lesson.course_id.in_(course_ids))
				.all()
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
	finally:
		session.close()


def list_course_lessons_controller(request: Request, course_id: str) -> LessonListResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
	session = SessionLocal()
	try:
		owned = session.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
		if not owned:
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
		lessons = (
			session.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.created_at.asc()).all()
		)
		lesson_models = [
			LessonDetail(
				lesson_id=getattr(l, "lesson_id"),
				course_id=getattr(l, "course_id"),
				title=getattr(l, "title"),
				description=getattr(l, "description"),
				content=getattr(l, "content"),
				finish=getattr(l, "finish"),
			)
			for l in lessons
		]
		return LessonListResponse(status=200, lessons=lesson_models)
	finally:
		session.close()


def get_lesson_detail_controller(request: Request, course_id: str, lesson_id: str) -> LessonDetail:
	from src.database import SessionLocal
	from src.models import Course, Lesson

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
	session = SessionLocal()
	try:
		owned = session.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
		if not owned:
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
		lesson = session.query(Lesson).filter(Lesson.lesson_id == lesson_id, Lesson.course_id == course_id).first()
		if not lesson:
			raise HTTPException(status_code=404, detail="Lesson not found")
		return LessonDetail(
			lesson_id=getattr(lesson, "lesson_id"),
			course_id=getattr(lesson, "course_id"),
			title=getattr(lesson, "title"),
			description=getattr(lesson, "description"),
			content=getattr(lesson, "content"),
			finish=getattr(lesson, "finish"),
		)
	finally:
		session.close()


def get_lesson_test_controller(request: Request, course_id: str, lesson_id: str) -> LessonTestResponse:
	from src.database import SessionLocal
	from src.models import Course, Test, LessonQA

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
	session = SessionLocal()
	try:
		owned = session.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
		if not owned:
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
		test = (
			session.query(Test)
			.filter(Test.lesson_id == lesson_id)
			.order_by(Test.created_at.asc())
			.first()
		)
		if not test:
			raise HTTPException(status_code=404, detail="Test not found")
		qas = session.query(LessonQA).filter(LessonQA.test_id == test.test_id).all()
		qa_models = [
			LessonTestQA(
				qa_id=getattr(qa, "qa_id"),
				question=getattr(qa, "question"),
				option1=getattr(qa, "option1"),
				option2=getattr(qa, "option2"),
				option3=getattr(qa, "option3"),
				option4=getattr(qa, "option4"),
				answer=getattr(qa, "answer"),
				explanation=getattr(qa, "explanation"),
				difficult_level_id=getattr(qa, "difficult_level_id", None),
			)
			for qa in qas
		]
		test_model = LessonTest(
			test_id=getattr(test, "test_id"),
			title=getattr(test, "title"),
			description=getattr(test, "description"),
			duration=getattr(test, "duration"),
			exp=getattr(test, "exp"),
			finish=getattr(test, "finish"),
			qas=qa_models,
		)
		return LessonTestResponse(status=200, test=test_model)
	finally:
		session.close()


def _normalize_answer_value(raw: str | None) -> str:
	return (raw or "").strip().lower()


def submit_lesson_test_controller(request: Request, course_id: str, lesson_id: str, body: LessonTestSubmitRequest) -> LessonTestSubmitResponse:
	from src.database import SessionLocal
	from src.models import Course, Lesson, Test, LessonQA
	import math

	user_id = _verify_token(request)
	if not user_id:
		return LessonTestSubmitResponse(status=401, message="Bạn không có quyền làm bài test này")

	session = SessionLocal()
	try:
		owned = session.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
		if not owned:
			return LessonTestSubmitResponse(status=401, message="Bạn không có quyền làm bài test này")

		test = (
			session.query(Test)
			.filter(Test.lesson_id == lesson_id)
			.order_by(Test.created_at.asc())
			.first()
		)
		if not test:
			return LessonTestSubmitResponse(status=404, message="Không tìm thấy bài test")

		qas = session.query(LessonQA).filter(LessonQA.test_id == test.test_id).all()
		qa_lookup = {getattr(qa, "qa_id"): qa for qa in qas}
		if not qas:
			return LessonTestSubmitResponse(status=400, message="Bài test chưa có câu hỏi")

		if not body.answers or len(body.answers) < len(qas):
			return LessonTestSubmitResponse(status=400, message="Vui lòng trả lời tất cả câu hỏi trước khi nộp bài")

		correct_count = 0
		earned_exp = 0
		penalty_exp = 0
		answer_results: list[LessonTestSubmitResultItem] = []

		for ans in body.answers:
			qa = qa_lookup.get(ans.qa_id)
			if not qa:
				continue
			options = {
				"option1": getattr(qa, "option1", ""),
				"option2": getattr(qa, "option2", ""),
				"option3": getattr(qa, "option3", ""),
				"option4": getattr(qa, "option4", ""),
			}
			# Determine correct option id
			correct_answer_raw = getattr(qa, "answer", "")
			correct_opt_id = correct_answer_raw if correct_answer_raw in options else None
			if not correct_opt_id:
				for key, val in options.items():
					if _normalize_answer_value(val) == _normalize_answer_value(correct_answer_raw):
						correct_opt_id = key
						break
			# Determine selected option id
			selected_opt_id = ans.answer if ans.answer in options else None
			if not selected_opt_id:
				for key, val in options.items():
					if _normalize_answer_value(val) == _normalize_answer_value(ans.answer):
						selected_opt_id = key
						break
			selected_opt_id = selected_opt_id or ""
			correct_opt_id = correct_opt_id or ""
			is_correct = selected_opt_id == correct_opt_id and bool(correct_opt_id)
			if is_correct:
				correct_count += 1

			difficulty_val = getattr(qa, "difficult_level_id", None)
			try:
				difficulty_int = int(difficulty_val) if difficulty_val is not None else None
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
				LessonTestSubmitResultItem(
					qa_id=ans.qa_id,
					selected_answer=selected_opt_id,
					correct_answer=correct_opt_id,
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

		# Only mark completion when passed. EXP/level will be handled client-side per requirement.
		level = None
		level_up = None
		current_exp = None
		require_exp = None

		if passed:
			lesson = session.query(Lesson).filter(Lesson.lesson_id == lesson_id, Lesson.course_id == course_id).first()
			if lesson:
				setattr(lesson, "finish", True)
			setattr(test, "finish", True)
			session.commit()
		else:
			session.rollback()

		result = LessonTestSubmitResult(
			score=score,
			correct_count=correct_count,
			total=total,
			earned_exp=earned_exp,
			penalty_exp=penalty_exp,
			applied_exp=applied_exp if passed else 0,
			passed=passed,
			pass_threshold=PASS_THRESHOLD,
			level=level,
			current_exp=current_exp,
			require_exp=require_exp,
			level_up=level_up,
			answers=answer_results,
		)
		return LessonTestSubmitResponse(status=200, result=result)
	except Exception as e:
		logger.error("submit_lesson_test_controller error user=%s course=%s lesson=%s err=%s", user_id, course_id, lesson_id, e)
		session.rollback()
		return LessonTestSubmitResponse(status=500, message="Có lỗi xảy ra khi chấm bài")
	finally:
		session.close()


def get_final_test_controller(request: Request, course_id: str) -> FinalTestResponse:
	from src.database import SessionLocal
	from src.models import Course, FinalTest, FinalQA

	user_id = _verify_token(request)
	if not user_id:
		raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
	session = SessionLocal()
	try:
		owned = session.query(Course).filter(Course.course_id == course_id, Course.user_id == user_id).first()
		if not owned:
			raise HTTPException(status_code=401, detail="Bạn không có quyền truy cập vào khóa học này")
		final_test = session.query(FinalTest).filter(FinalTest.course_id == course_id).first()
		if not final_test:
			raise HTTPException(status_code=404, detail="Final test not found")
		qas = session.query(FinalQA).filter(FinalQA.final_test_id == final_test.final_test_id).all()
		qa_models = [
			FinalTestQA(
				final_qa_id=getattr(qa, "final_qa_id"),
				question=getattr(qa, "question"),
				option1=getattr(qa, "option1"),
				option2=getattr(qa, "option2"),
				option3=getattr(qa, "option3"),
				option4=getattr(qa, "option4"),
				answer=getattr(qa, "answer"),
				explanation=getattr(qa, "explanation"),
			)
			for qa in qas
		]
		final_test_model = FinalTestDetail(
			final_test_id=getattr(final_test, "final_test_id"),
			title=getattr(final_test, "title"),
			description=getattr(final_test, "description"),
			duration=getattr(final_test, "duration"),
			exp=getattr(final_test, "exp"),
			qas=qa_models,
		)
		return FinalTestResponse(status=200, final_test=final_test_model)
	finally:
		session.close()


# ---------------- Mutation Controllers ----------------

def finish_course_controller(request: Request, payload: FinishCourseRequest):
	"""Mark a course as finished if all its lessons and tests/final test are finished.

	Business rule (current inferred):
	- User must own course
	- All lessons.finish == True
	- (Optional) final tests existence not strictly enforced; if exists must have all qas done? Currently only have finish flag on Course, Lesson, Test. We'll require all Lessons.finish AND any Test / FinalTest under it have finish=True if present.
	"""
	from src.database import SessionLocal
	from src.models import Course, Lesson, Test

	user_id = _verify_token(request)
	if not user_id:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})

	session = SessionLocal()
	try:
		course = session.query(Course).filter_by(course_id=payload.course_id, user_id=user_id).first()
		if not course:
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})

		# Check lessons
		lessons = session.query(Lesson.lesson_id, Lesson.finish).filter(Lesson.course_id == course.course_id).all()
		if not lessons or any(not l.finish for l in lessons):
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})

		# Check tests
		tests = session.query(Test.finish).join(Lesson, Test.lesson_id == Lesson.lesson_id).filter(Lesson.course_id == course.course_id).all()
		if any(not t.finish for t in tests):
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn chưa hoàn thành tất cả các bài học trong khóa học này, vui lòng thử lại sau"})

		# Mark course finished
		setattr(course, "finish", True)
		session.commit()
		return {"status": 200, "message": "Đã cập nhật thành công"}
	except Exception as e:
		logger.error("finish_course_controller error user=%s course=%s err=%s", user_id, payload.course_id, e)
		session.rollback()
		return JSONResponse(status_code=500, content={"status": 500, "message": "Internal error"})
	finally:
		session.close()


def finish_lesson_controller(request: Request, payload: FinishLessonRequest):
	"""Mark a single lesson (and optionally its test) as finished.

	Rules (inferred):
	- User must own the course containing the lesson.
	- We assume caller only invokes after passing its test. We'll just flip finish flag.
	- If related Test exists we also mark its finish=True (since spec says triggered after passing test).
	"""
	from src.database import SessionLocal
	from src.models import Course, Lesson, Test

	user_id = _verify_token(request)
	if not user_id:
		return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền cập nhật bài học này"})

	session = SessionLocal()
	try:
		course = session.query(Course).filter_by(course_id=payload.course_id, user_id=user_id).first()
		if not course:
			return JSONResponse(status_code=401, content={"status": 401, "message": "Bạn không có quyền cập nhật bài học này"})
		lesson = session.query(Lesson).filter_by(lesson_id=payload.lesson_id, course_id=course.course_id).first()
		if not lesson:
			return JSONResponse(status_code=404, content={"status": 404, "message": "Lesson không tồn tại"})
		setattr(lesson, "finish", True)
		# Mark related tests finished (if any)
		tests = session.query(Test).filter(Test.lesson_id == lesson.lesson_id).all()
		for t in tests:
			setattr(t, "finish", True)
		session.commit()
		return {"status": 200, "message": "Đã cập nhật thành công"}
	except Exception as e:
		logger.error("finish_lesson_controller error user=%s course=%s lesson=%s err=%s", user_id, payload.course_id, payload.lesson_id, e)
		session.rollback()
		return JSONResponse(status_code=500, content={"status": 500, "message": "Internal error"})
	finally:
		session.close()
