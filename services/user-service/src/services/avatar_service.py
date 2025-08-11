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

__all__ = ["update_avatar", "get_avatar_stream", "get_avatar_redirect", "get_avatar_bytes"]  # added get_avatar_bytes

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
    key = f"avatars/{avatar_id}.jpg"  # New: fixed key with .jpg extension
    try:
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
        # Delete old object if naming changed (backward compatibility)
        old_key = current_user.avatar_url
        if old_key and old_key != key:
            try:
                # If old_key stored only id, construct full path
                if '/' not in old_key and not old_key.lower().endswith(('.jpg', '.jpeg', '.png')):
                    legacy_full = f"avatars/{old_key}"
                    s3.delete_object(Bucket=bucket, Key=legacy_full)
                else:
                    s3.delete_object(Bucket=bucket, Key=old_key)
            except Exception as e:  # pragma: no cover
                logger.warning(f"Could not delete old avatar {old_key}: {e}")
    except Exception as e:  # pragma: no cover
        logger.error(f"Upload avatar failed: {e}")
        return 500, "Lỗi khi tải ảnh lên. Vui lòng thử lại"
    current_user.avatar_url = key  # always store full key
    db.commit()
    logger.info(f"Avatar updated: {current_user.email}")
    return 200, "Bạn đã cập nhật Avatar thành công"


def get_avatar_stream(avatar_id: str | None):
    """Stream avatar file from S3.
    If avatar_id contains '/', treat it as full key.
    If None, raise 404.
    Also allow root-level default files like male.png / female.png
    Added support for .jpg fixed naming; fallback to legacy key without extension.
    Refactored caching: user-specific avatars return no-store to avoid stale cache on same URL.
    """
    if not avatar_id:
        raise HTTPException(status_code=404, detail="Avatar không tồn tại")
    s3 = _get_s3_client()
    if not s3:
        raise HTTPException(status_code=500, detail="S3 client not available")
    bucket = config.S3_USER_BUCKET_NAME
    if not bucket:
        raise HTTPException(status_code=500, detail="S3 bucket not configured")

    if '/' in avatar_id:
        key = avatar_id
    elif avatar_id.lower().endswith(('.png', '.jpg', '.jpeg')):
        key = avatar_id
    else:
        key = f"avatars/{avatar_id}.jpg"

    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code')
        # Fallback: legacy key without extension
        if code in ('404', 'NoSuchKey') and key.endswith('.jpg'):
            legacy_key = key[:-4]  # remove .jpg
            try:
                obj = s3.get_object(Bucket=bucket, Key=legacy_key)
                key = legacy_key
            except ClientError as e2:
                code2 = e2.response.get('Error', {}).get('Code')
                if code2 in ('404', 'NoSuchKey'):
                    raise HTTPException(status_code=404, detail="Avatar không tồn tại")
                logger.error(f"S3 get_object error: {e2}")
                raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")
        else:
            if code in ('404', 'NoSuchKey'):
                raise HTTPException(status_code=404, detail="Avatar không tồn tại")
            logger.error(f"S3 get_object error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")

    body = obj['Body']
    def iter_chunks():
        for chunk in iter(lambda: body.read(8192), b""):
            yield chunk

    # Caching strategy (no long cache even for default male/female)
    headers = {"Cache-Control": "no-store"}
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

    # Build key similarly
    if '/' in avatar_id or avatar_id.lower().endswith(('.png', '.jpg', '.jpeg')):
        key = avatar_id
    else:
        key = f"avatars/{avatar_id}.jpg"

    try:
        s3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code')
        if code in ('404', 'NoSuchKey') and key.endswith('.jpg'):
            legacy_key = key[:-4]
            try:
                s3.head_object(Bucket=bucket, Key=legacy_key)
                key = legacy_key
            except ClientError as e2:
                code2 = e2.response.get('Error', {}).get('Code')
                if code2 in ('404', 'NoSuchKey'):
                    raise HTTPException(status_code=404, detail="Avatar không tồn tại")
                logger.error(f"S3 error: {e2.response['Error'].get('Message')}")
                raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")
        else:
            if code in ('404', 'NoSuchKey'):
                raise HTTPException(status_code=404, detail="Avatar không tồn tại")
            logger.error(f"S3 error: {e.response['Error'].get('Message')}")
            raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")

    try:
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
        return RedirectResponse(url=url)
    except Exception as e:  # pragma: no cover
        logger.error(f"Presign error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")

def get_avatar_bytes(avatar_id: str | None) -> tuple[bytes, str, dict]:
    """Fetch avatar and return raw bytes (non-streaming) for API Gateway/Lambda compatibility.
    Applies same caching policy as get_avatar_stream.
    Returns: (content_bytes, media_type, headers)
    Raises HTTPException on errors similar to get_avatar_stream.
    """
    if not avatar_id:
        raise HTTPException(status_code=404, detail="Avatar không tồn tại")
    s3 = _get_s3_client()
    if not s3:
        raise HTTPException(status_code=500, detail="S3 client not available")
    bucket = config.S3_USER_BUCKET_NAME
    if not bucket:
        raise HTTPException(status_code=500, detail="S3 bucket not configured")

    if '/' in avatar_id:
        key = avatar_id
    elif avatar_id.lower().endswith(('.png', '.jpg', '.jpeg')):
        key = avatar_id
    else:
        key = f"avatars/{avatar_id}.jpg"

    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code')
        if code in ('404', 'NoSuchKey') and key.endswith('.jpg'):
            legacy_key = key[:-4]
            try:
                obj = s3.get_object(Bucket=bucket, Key=legacy_key)
                key = legacy_key
            except ClientError as e2:
                code2 = e2.response.get('Error', {}).get('Code')
                if code2 in ('404', 'NoSuchKey'):
                    raise HTTPException(status_code=404, detail="Avatar không tồn tại")
                logger.error(f"S3 get_object error: {e2}")
                raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")
        else:
            if code in ('404', 'NoSuchKey'):
                raise HTTPException(status_code=404, detail="Avatar không tồn tại")
            logger.error(f"S3 get_object error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")

    try:
        content_bytes = obj['Body'].read()
    except Exception as e:  # pragma: no cover
        logger.error(f"Read S3 body error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi truy cập avatar")

    filename = key.rsplit('/', 1)[-1]
    # Unified caching: disable long cache for all avatars (including defaults)
    headers: dict = {"Cache-Control": "no-store"}
    etag = obj.get('ETag')
    if etag:
        headers['ETag'] = etag.strip('"')
    media_type = obj.get('ContentType', 'image/jpeg')
    return content_bytes, media_type, headers
