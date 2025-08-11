"""Avatar service: handling image validation, processing & S3 storage."""
from __future__ import annotations
import io
import uuid
import logging
from typing import Optional
from PIL import Image
from fastapi import UploadFile, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse  # added StreamingResponse
import boto3
from botocore.exceptions import ClientError
from config import config
from models import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MAX_SIZE_MB = 3
TARGET_SIZE = (400, 400)
ALLOWED_PREFIX = 'image/'

__all__ = ["update_avatar", "get_avatar_stream", "get_avatar_redirect"]  # added get_avatar_stream

def _get_s3_client():
    try:
        if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
            return boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
        return boto3.client('s3', region_name=config.AWS_REGION)
    except Exception as e:  # pragma: no cover
        logger.error(f"S3 client error: {e}")
        return None

def _process_image(raw: bytes) -> io.BytesIO:
    try:
        img = Image.open(io.BytesIO(raw))
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', optimize=True, quality=85)
        buf.seek(0)
        return buf
    except Exception as e:
        raise HTTPException(status_code=400, detail="Không thể xử lý ảnh") from e

def update_avatar(avatar_file: UploadFile, current_user: User, db: Session) -> tuple[int, str]:
    if not avatar_file.content_type or not avatar_file.content_type.startswith(ALLOWED_PREFIX):
        return 400, "File phải là ảnh (JPG, PNG, WebP)"
    raw = avatar_file.file.read()
    if len(raw) > MAX_SIZE_MB * 1024 * 1024:
        return 400, "Kích thước ảnh không được vượt quá 3MB"
    s3 = _get_s3_client()
    if not s3:
        return 500, "Không thể kết nối đến dịch vụ lưu trữ"
    bucket = config.S3_USER_BUCKET_NAME
    if not bucket:
        return 500, "Cấu hình lưu trữ không đầy đủ"
    processed = _process_image(raw)
    avatar_id = str(current_user.id)
    try:
        key = f"avatars/{avatar_id}"
        s3.upload_fileobj(
            processed,
            bucket,
            key,
            ExtraArgs={
                'ContentType': 'image/jpeg',
                'CacheControl': 'public, max-age=31536000',
                'Metadata': {
                    'user_id': str(current_user.id),
                    'user_email': current_user.email,
                    'upload_timestamp': str(uuid.uuid1().time),
                    'original_filename': avatar_file.filename or 'unknown'
                }
            }
        )
    except Exception as e:  # pragma: no cover
        logger.error(f"Upload avatar failed: {e}")
        return 500, "Lỗi khi tải ảnh lên. Vui lòng thử lại"
    current_user.avatar_url = key  # store full key instead of only id
    db.commit()
    logger.info(f"Avatar updated: {current_user.email}")
    return 200, "Bạn đã cập nhật Avatar thành công"


def get_avatar_stream(avatar_id: str | None):
    """Stream avatar file from S3.
    If avatar_id contains '/', treat it as full key.
    If None, raise 404.
    Also allow root-level default files like male.png / female.png
    """
    if not avatar_id:
        raise HTTPException(status_code=404, detail="Avatar không tồn tại")
    s3 = _get_s3_client()
    if not s3:
        raise HTTPException(status_code=500, detail="S3 client not available")
    bucket = config.S3_USER_BUCKET_NAME
    if not bucket:
        raise HTTPException(status_code=500, detail="S3 bucket not configured")
    # If file looks like a default (endswith .png and no slash) keep as-is
    if '/' in avatar_id or avatar_id.endswith('.png'):
        key = avatar_id
    else:
        key = f"avatars/{avatar_id}"
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code')
        if code in ('404', 'NoSuchKey'):
            raise HTTPException(status_code=404, detail="Avatar không tồn tại")
        logger.error(f"S3 get_object error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")
    body = obj['Body']
    def iter_chunks():
        for chunk in iter(lambda: body.read(8192), b""):
            yield chunk
    headers = {"Cache-Control": "public, max-age=31536000"}
    etag = obj.get('ETag')
    if etag:
        headers['ETag'] = etag.strip('"')
    return StreamingResponse(iter_chunks(), media_type=obj.get('ContentType', 'image/jpeg'), headers=headers)

def get_avatar_redirect(avatar_id: str):
    s3 = _get_s3_client()
    if not s3:
        raise HTTPException(status_code=500, detail="S3 client not available")
    bucket = config.S3_USER_BUCKET_NAME
    if not bucket:
        raise HTTPException(status_code=500, detail="S3 bucket not configured")
    key = f"avatars/{avatar_id}"
    try:
        s3.head_object(Bucket=bucket, Key=key)
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
        return RedirectResponse(url=url)
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            raise HTTPException(status_code=404, detail="Avatar không tồn tại")
        logger.error(f"S3 error: {e.response['Error'].get('Message')}")
        raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")
