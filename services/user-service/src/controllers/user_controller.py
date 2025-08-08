import logging
import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from PIL import Image
import io
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import requests
from jose import jwt
from datetime import datetime, timedelta

from models import User
from schemas.user_schemas import *
from config import config

logger = logging.getLogger(__name__)

# ===== LEVEL SYSTEM CONFIGURATION =====
LEVEL_EXP_THRESHOLDS = [
    0,      # Level 1: 0 exp
    100,    # Level 2: 100 exp
    300,    # Level 3: 300 exp
    600,    # Level 4: 600 exp
    1000,   # Level 5: 1000 exp
    1500,   # Level 6: 1500 exp
    2100,   # Level 7: 2100 exp
    2800,   # Level 8: 2800 exp
    3600,   # Level 9: 3600 exp
    4500,   # Level 10: 4500 exp
    5500,   # Level 11: 5500 exp
    6600,   # Level 12: 6600 exp
    7800,   # Level 13: 7800 exp
    9100,   # Level 14: 9100 exp
    10500,  # Level 15: 10500 exp
]

def get_exp_for_level(level: int) -> int:
    if level <= 1:
        return 0
    
    level_index = level - 1
    
    if level_index < len(LEVEL_EXP_THRESHOLDS):
        return LEVEL_EXP_THRESHOLDS[level_index]
    
    base_level = len(LEVEL_EXP_THRESHOLDS)
    base_exp = LEVEL_EXP_THRESHOLDS[-1]
    growth_factor = 1.3 
    
    additional_levels = level - base_level
    additional_exp = base_exp * (growth_factor ** additional_levels) - base_exp
    
    return int(base_exp + additional_exp)

def calculate_level_from_exp(current_exp: int) -> tuple[int, int, int]:
    if current_exp <= 0:
        return 1, 0, get_exp_for_level(2)
    
    level = 1
    while True:
        next_level_exp = get_exp_for_level(level + 1)
        if current_exp < next_level_exp:
            break
        level += 1
        
        if level > 1000:
            break
    
    current_level_exp = get_exp_for_level(level)
    next_level_exp = get_exp_for_level(level + 1)
    
    return level, current_level_exp, next_level_exp

from typing import Optional

def auto_level_up(current_exp: int, current_level: Optional[int] = None) -> tuple[int, int, bool]:
    new_level, current_level_exp, next_level_exp = calculate_level_from_exp(current_exp)
    
    level_increased = current_level is not None and new_level > current_level
    
    return new_level, next_level_exp, level_increased

def create_access_token(email: str) -> str:
    try:
        expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode = {
            "sub": email,
            "exp": expire,
            "type": "access"
        }
        encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        return ""

def get_s3_client():
    try:
        if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
            return boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
        return boto3.client('s3', region_name=config.AWS_REGION)
    except Exception as e:
        logger.error(f"S3 client error: {e}")
        return None

async def change_user_info(request: ChangeInfoRequest, current_user: User, db: Session) -> MessageResponse:
    try:
        if request.family_name is not None:
            setattr(current_user, 'family_name', request.family_name)
        if request.given_name is not None:
            setattr(current_user, 'given_name', request.given_name)
        if request.dob is not None:
            setattr(current_user, 'dob', request.dob)
        if request.sex is not None:
            setattr(current_user, 'sex', request.sex)
        if request.bio is not None:
            setattr(current_user, 'bio', request.bio)
        db.commit()
        logger.info(f"User info updated: {current_user.email}")
        return MessageResponse(status=200, message="Bạn đã đổi thông tin cá nhân thành công")
    except Exception as e:
        logger.error(f"Update info failed: {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        db.rollback()
        return MessageResponse(status=401, message="Có lỗi xảy ra, xin vui lòng thử lại")

async def get_user_avatar(avatar_id: str):
    try:
        s3_client = get_s3_client()
        if not s3_client:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="S3 client not available")
        bucket_name = config.S3_USER_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="S3 bucket not configured")
        avatar_key = f"avatars/{avatar_id}"
        try:
            s3_client.head_object(Bucket=bucket_name, Key=avatar_key)
            presigned_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': avatar_key}, ExpiresIn=3600)
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=presigned_url)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"Avatar not found: {avatar_key}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar không tồn tại")
            logger.error(f"S3 error: {e.response['Error']['Message']}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lỗi khi truy cập avatar")
    except Exception as e:
        logger.error(f"Avatar error {avatar_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy ảnh")

async def update_user_avatar(avatar_file: UploadFile, current_user: User, db: Session) -> MessageResponse:
    try:
        if not avatar_file.content_type or not avatar_file.content_type.startswith('image/'):
            return MessageResponse(status=400, message="File phải là ảnh (JPG, PNG, WebP)")
        contents = await avatar_file.read()
        if len(contents) > 3 * 1024 * 1024:
            return MessageResponse(status=400, message="Kích thước ảnh không được vượt quá 3MB")
        s3_client = get_s3_client()
        if not s3_client:
            return MessageResponse(status=500, message="Không thể kết nối đến dịch vụ lưu trữ")
        bucket_name = config.S3_USER_BUCKET_NAME
        if not bucket_name:
            return MessageResponse(status=500, message="Cấu hình lưu trữ không đầy đủ")
        avatar_id = str(current_user.id)
        try:
            image = Image.open(io.BytesIO(contents))
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            image = image.resize((400, 400), Image.Resampling.LANCZOS)
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', optimize=True, quality=85)
            img_buffer.seek(0)
        except Exception:
            return MessageResponse(status=400, message="Không thể xử lý ảnh. Vui lòng thử ảnh khác")
        try:
            s3_key = f"avatars/{avatar_id}"
            s3_client.upload_fileobj(
                img_buffer,
                bucket_name,
                s3_key,
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
        except Exception:
            return MessageResponse(status=500, message="Lỗi khi tải ảnh lên. Vui lòng thử lại")
        current_user.avatar_url = avatar_id
        db.commit()
        logger.info(f"Avatar updated: {current_user.email}")
        return MessageResponse(status=200, message="Bạn đã cập nhật Avatar thành công")
    except Exception:
        db.rollback()
        return MessageResponse(status=500, message="Có lỗi xảy ra khi tải ảnh lên, xin vui lòng thử lại")

async def get_user_info(user_id: Optional[str], current_user: User, db: Session) -> UserInfoResponse:
    try:
        target_user = current_user
        if user_id:
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                return UserInfoResponse(
                    status=401,
                    message="Người dùng không tồn tại"
                )
        
        dob_formatted = None
        if getattr(target_user, 'dob', None):
            dob_formatted = getattr(target_user, 'dob').strftime("%d/%m/%Y")
        
        avatar_url = None
        avatar_id = getattr(target_user, 'avatar_url', None)
        if avatar_id:
            if avatar_id.startswith('http'):
                avatar_url = avatar_id
            else:
                avatar_url = f"{config.USER_SERVICE_URL}/avatar/?user_id={target_user.id}"
        
        user_info = {
            "id": getattr(target_user, 'id', None),
            "email": getattr(target_user, 'email', None),
            "family_name": getattr(target_user, 'family_name', None),
            "given_name": getattr(target_user, 'given_name', None),
            "birth_date": dob_formatted,
            "avatar_id": avatar_id,
            "avatar_url": avatar_url,
            "level": getattr(target_user, 'level', 1),
            "current_exp": getattr(target_user, 'current_exp', 0),
            "require_exp": getattr(target_user, 'require_exp', 1000),
            "sex": getattr(target_user, 'sex', None),
            "bio": getattr(target_user, 'bio', None),
            "remind_time": getattr(target_user, 'remind_time', None),
            "created_at": getattr(target_user, 'created_at', None)
        }
        
        return UserInfoResponse(
            status=200,
            Info=user_info
        )
        
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return UserInfoResponse(
            status=401,
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )

async def get_all_users(db: Session) -> UsersListResponse:
    try:
        users = db.query(User).filter(User.is_active == True).all()
        
        users_info = []
        for user in users:
            dob_formatted = None
            if getattr(user, 'dob', None):
                dob_formatted = getattr(user, 'dob').strftime("%d/%m/%Y")
            
            avatar_url = None
            avatar_id = getattr(user, 'avatar_url', None)
            if avatar_id:
                if avatar_id.startswith('http'):
                    avatar_url = avatar_id
                else:
                    avatar_url = f"{config.USER_SERVICE_URL}/avatar/?user_id={user.id}"
                
            user_data = {
                "user_id": getattr(user, 'id', None),
                "family_name": getattr(user, 'family_name', None),
                "given_name": getattr(user, 'given_name', None),
                "dob": dob_formatted,
                "avatar_id": avatar_id,
                "avatar_url": avatar_url,
                "level": getattr(user, 'level', 1),
                "current_exp": getattr(user, 'current_exp', 0),
                "require_exp": getattr(user, 'require_exp', 1000),
                "sex": getattr(user, 'sex', None),
                "bio": getattr(user, 'bio', None),
                "remind_time": getattr(user, 'remind_time', None)
            }
            users_info.append(user_data)
        
        return UsersListResponse(
            status=200,
            infos=users_info
        )
        
    except Exception as e:
        logger.error(f"Error getting all users: {str(e)}")
        return UsersListResponse(
            status=401,
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )

async def set_notify_time(request: NotifyTimeRequest, current_user: User, db: Session) -> MessageResponse:
    try:
        setattr(current_user, 'remind_time', request.remind_time)
        db.commit()
        logger.info(f"Successfully set remind time for user {current_user.email} to {request.remind_time}")
        return MessageResponse(
            status=200,
            message="Đã đặt lịch thành công"
        )
        
    except Exception as e:
        logger.error(f"Failed to set remind time for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        db.rollback()
        return MessageResponse(
            status=401,
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )

async def get_user_dashboard(current_user: User, db: Session) -> DashboardResponse:
    try:
        avatar_url = None
        avatar_id = getattr(current_user, 'avatar_url', None)
        if avatar_id:
            if avatar_id.startswith('http'):
                avatar_url = avatar_id
            else:
                avatar_url = f"{config.USER_SERVICE_URL}/avatar/?user_id={current_user.id}"
        course_stats = await get_course_stats(current_user.email)
        quiz_stats = await get_quiz_stats(current_user.email)
        rank_data = await calculate_user_rank(current_user, db)
        leaderboard = await get_leaderboard_data(db)
        
        # Calculate real dashboard data
        dashboard_info = {
            "id": current_user.id,
            "email": current_user.email,
            "level": getattr(current_user, 'level', 1),
            "current_exp": getattr(current_user, 'current_exp', 0),
            "require_exp": getattr(current_user, 'require_exp', 100),
            "family_name": getattr(current_user, 'family_name', None),
            "given_name": getattr(current_user, 'given_name', None),
            "avatar_url": avatar_url,
            "remind_time": getattr(current_user, 'remind_time', None),
            
            # Real course statistics
            "course_num": course_stats["total_courses"],
            "total_courses": course_stats["total_courses"],
            "finish_course_num": course_stats["completed_courses"],
            "completed_courses": course_stats["completed_courses"],
            "lesson_num": course_stats["total_lessons"],
            
            # Real quiz statistics
            "quiz_num": quiz_stats["total_quizzes"],
            "total_quizzes": quiz_stats["total_quizzes"],
            "completed_quizzes": quiz_stats["completed_quizzes"],
            "average_quiz_score": quiz_stats["average_score"],
            "average_score": quiz_stats["average_score"],
            
            # Real ranking data
            "rank": rank_data["rank"],
            "user_num": rank_data["total_users"],
            
            # Leaderboard data for display
            "user_top_rank": leaderboard,
            
            # Activity data placeholder
            "learning_history": [],
        }
        
        return DashboardResponse(
            status=200,
            info=dashboard_info
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        return DashboardResponse(
            status=401,
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )

async def save_user_activity(current_user: User, db: Session) -> MessageResponse:
    try:
        return MessageResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error saving activity for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        return MessageResponse(
            status=401,
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )

async def get_course_stats(user_email: str) -> dict:
    try:
        course_service_url = f"{config.COURSE_SERVICE_URL}/api/v1"
        headers = {"Authorization": f"Bearer {create_access_token(user_email)}"}
        
        courses_response = requests.get(f"{course_service_url}/courses", headers=headers, timeout=5)
        courses_data = courses_response.json() if courses_response.status_code == 200 else {"courses": []}
        
        total_courses = len(courses_data.get("courses", []))
        
        results_response = requests.get(f"{course_service_url}/user/test-results", headers=headers, timeout=5)
        results_data = results_response.json() if results_response.status_code == 200 else {"results": []}
        
        completed_courses = len(set(result.get("test_id") for result in results_data.get("results", [])))
        
        total_lessons = 0
        for course in courses_data.get("courses", []):
            course_id = course.get("id")
            if course_id:
                lessons_response = requests.get(f"{course_service_url}/courses/{course_id}/lessons", headers=headers, timeout=5)
                lessons_data = lessons_response.json() if lessons_response.status_code == 200 else {"lessons": []}
                total_lessons += len(lessons_data.get("lessons", []))
        
        return {
            "total_courses": total_courses,
            "completed_courses": completed_courses,
            "total_lessons": total_lessons
        }
    except Exception as e:
        logger.error(f"Error getting course stats: {str(e)}")
        return {"total_courses": 0, "completed_courses": 0, "total_lessons": 0}

async def get_quiz_stats(user_email: str) -> dict:
    try:
        quiz_service_url = f"{config.QUIZ_SERVICE_URL}/api/v1"
        headers = {"Authorization": f"Bearer {create_access_token(user_email)}"}
        
        quizzes_response = requests.get(f"{quiz_service_url}/quizzes", headers=headers, timeout=5)
        quizzes_data = quizzes_response.json() if quizzes_response.status_code == 200 else {"quizzes": []}
        
        total_quizzes = len(quizzes_data.get("quizzes", []))
        
        attempts_response = requests.get(f"{quiz_service_url}/user/quiz-attempts", headers=headers, timeout=5)
        attempts_data = attempts_response.json() if attempts_response.status_code == 200 else {"attempts": []}
        
        attempts = attempts_data.get("attempts", [])
        completed_quizzes = len(attempts)
        
        total_score = sum(attempt.get("score", 0) for attempt in attempts)
        average_score = total_score / len(attempts) if attempts else 0
        
        return {
            "total_quizzes": total_quizzes,
            "completed_quizzes": completed_quizzes,
            "average_score": average_score / 100 if average_score > 1 else average_score 
        }
    except Exception as e:
        logger.error(f"Error getting quiz stats: {str(e)}")
        return {"total_quizzes": 0, "completed_quizzes": 0, "average_score": 0}

async def calculate_user_rank(current_user: User, db: Session) -> dict:
    try:
        users = db.query(User).filter(User.is_active == True).order_by(User.current_exp.desc()).all()
        
        user_rank = 1
        total_users = len(users)
        
        for i, user in enumerate(users):
            if user.id == current_user.id:
                user_rank = i + 1
                break
        
        return {"rank": user_rank, "total_users": total_users}
    except Exception as e:
        logger.error(f"Error calculating user rank: {str(e)}")
        return {"rank": 1, "total_users": 1}

async def get_leaderboard_data(db: Session) -> list:
    try:
        top_users = db.query(User).filter(User.is_active == True).order_by(User.current_exp.desc()).limit(10).all()
        
        leaderboard = []
        for i, user in enumerate(top_users):
            avatar_url = None
            if user.avatar_url:
                if user.avatar_url.startswith('http'):
                    avatar_url = user.avatar_url
                else:
                    avatar_url = f"{config.USER_SERVICE_URL}/avatar/?user_id={user.id}"
            
            leaderboard.append({
                "rank": i + 1,
                "id": str(user.id),
                "name": f"{user.family_name or ''} {user.given_name or ''}".strip() or user.email.split('@')[0],
                "level": user.level or 1,
                "experience": user.current_exp or 0,
                "avatar_url": avatar_url,
                "initials": "".join([name[0].upper() for name in [user.family_name or '', user.given_name or ''] if name])[:2] or user.email[0].upper()
            })
        
        return leaderboard
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        return []

async def get_users_by_ids(user_ids: list[str], db: Session) -> dict:
    try:
        users = db.query(User).filter(User.id.in_(user_ids), User.is_active == True).all()
        user_data = {}
        for user in users:
            avatar_url = None
            avatar_id = getattr(user, 'avatar_url', None)
            if avatar_id:
                if avatar_id.startswith('http'):
                    avatar_url = avatar_id
                else:
                    avatar_url = f"{config.USER_SERVICE_URL}/avatar/?user_id={user.id}"
            
            user_data[str(user.id)] = {
                "id": str(user.id),
                "name": f"{user.family_name or ''} {user.given_name or ''}".strip() or user.email.split('@')[0],
                "avatar_url": avatar_url,
                "level": user.level or 1,
                "initials": "".join([name[0].upper() for name in [user.family_name or '', user.given_name or ''] if name])[:2] or user.email[0].upper()
            }
        
        return user_data
    except Exception as e:
        logger.error(f"Error getting users by IDs: {str(e)}")
        return {}

async def update_test_stats(request: TestStatsRequest, current_user: User, db: Session) -> TestStatsResponse:
    try:
        original_stats = {
            "level": getattr(current_user, 'level', 1),
            "current_exp": getattr(current_user, 'current_exp', 0),
            "require_exp": getattr(current_user, 'require_exp', 100),
        }
        
        calculated_exp = 0
        if request.current_exp is not None:
            calculated_exp = request.current_exp
        else:
            if request.completed_courses:
                calculated_exp += request.completed_courses * 100
            
            if request.completed_quizzes:
                calculated_exp += request.completed_quizzes * 50
            
            if request.average_score and request.completed_quizzes:
                score_bonus = int(request.average_score * request.completed_quizzes * 25)
                calculated_exp += score_bonus
            
            if request.total_lessons:
                lesson_exp = request.total_lessons * 10
                calculated_exp += lesson_exp
        
        final_exp = calculated_exp
        if request.current_exp is not None or calculated_exp > 0:
            final_exp = calculated_exp
            setattr(current_user, 'current_exp', final_exp)
        else:
            final_exp = getattr(current_user, 'current_exp', 0)
        
        level_changed = False
        if request.level is not None:
            setattr(current_user, 'level', request.level)
            next_level_exp = get_exp_for_level(request.level + 1)
            setattr(current_user, 'require_exp', next_level_exp)
        else:
            current_level = getattr(current_user, 'level', 1)
            new_level, next_level_exp, level_increased = auto_level_up(final_exp, current_level)
            
            setattr(current_user, 'level', new_level)
            setattr(current_user, 'require_exp', next_level_exp)
            level_changed = level_increased
        
        if request.require_exp is not None:
            setattr(current_user, 'require_exp', request.require_exp)
        
        test_data = {}
        if request.total_courses is not None:
            test_data['test_total_courses'] = request.total_courses
        if request.completed_courses is not None:
            test_data['test_completed_courses'] = request.completed_courses
        if request.total_lessons is not None:
            test_data['test_total_lessons'] = request.total_lessons
        if request.total_quizzes is not None:
            test_data['test_total_quizzes'] = request.total_quizzes
        if request.completed_quizzes is not None:
            test_data['test_completed_quizzes'] = request.completed_quizzes
        if request.average_score is not None:
            test_data['test_average_score'] = request.average_score
        
        if test_data:
            import json
            current_bio = getattr(current_user, 'bio', '') or ''
            if current_bio and not current_bio.endswith('\n'):
                current_bio += '\n'
            current_bio += f"[TEST_DATA] {json.dumps(test_data)}"
            setattr(current_user, 'bio', current_bio)
        
        db.commit()
        
        updated_stats = {
            "level": getattr(current_user, 'level'),
            "current_exp": getattr(current_user, 'current_exp'),
            "require_exp": getattr(current_user, 'require_exp'),
            "calculated_exp_from_activities": calculated_exp if request.current_exp is None else None,
            "level_changed": level_changed,
            "original_stats": original_stats
        }
        
        rank_data = await calculate_user_rank(current_user, db)
        updated_stats.update(rank_data)
        
        level_msg = ""
        if level_changed:
            level_msg = f" 🎉 LEVEL UP! {original_stats['level']} → {updated_stats['level']}"
        
        logger.info(f"Successfully updated test stats for user {current_user.email}: {updated_stats}")
        
        return TestStatsResponse(
            status=200,
            message=f"Cập nhật thành công! Level: {updated_stats['level']}, Exp: {updated_stats['current_exp']}, Rank: {updated_stats['rank']}{level_msg}",
            updated_stats=updated_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to update test stats for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        db.rollback()
        return TestStatsResponse(
            status=500,
            message="Có lỗi xảy ra khi cập nhật thống kê test"
        )

async def reset_test_stats(current_user: User, db: Session) -> TestStatsResponse:
    try:
        setattr(current_user, 'level', 1)
        setattr(current_user, 'current_exp', 0)
        setattr(current_user, 'require_exp', get_exp_for_level(2))
        
        current_bio = getattr(current_user, 'bio', '') or ''
        bio_lines = current_bio.split('\n')
        filtered_lines = [line for line in bio_lines if not line.startswith('[TEST_DATA]')]
        setattr(current_user, 'bio', '\n'.join(filtered_lines).strip())
        
        db.commit();
        
        rank_data = await calculate_user_rank(current_user, db);
        
        reset_stats = {
            "level": 1,
            "current_exp": 0,
            "require_exp": get_exp_for_level(2),
            **rank_data
        };
        
        logger.info(f"Successfully reset test stats for user {current_user.email}");
        
        return TestStatsResponse(
            status=200,
            message="Đã reset thống kê về mặc định",
            updated_stats=reset_stats
        );
        
    except Exception as e:
        logger.error(f"Failed to reset test stats for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        db.rollback()
        return TestStatsResponse(
            status=500,
            message="Có lỗi xảy ra khi reset thống kê"
        )

async def get_level_system_info() -> dict:
    try:
        level_info = []
        for i, exp in enumerate(LEVEL_EXP_THRESHOLDS):
            level = i + 1
            next_exp = get_exp_for_level(level + 1) if level < len(LEVEL_EXP_THRESHOLDS) else get_exp_for_level(level + 1)
            level_info.append({
                "level": level,
                "required_exp": exp,
                "next_level_exp": next_exp,
                "exp_to_next": next_exp - exp
            })
        
        for level in range(len(LEVEL_EXP_THRESHOLDS) + 1, len(LEVEL_EXP_THRESHOLDS) + 6):
            exp = get_exp_for_level(level)
            next_exp = get_exp_for_level(level + 1)
            level_info.append({
                "level": level,
                "required_exp": exp,
                "next_level_exp": next_exp,
                "exp_to_next": next_exp - exp,
                "calculated": True
            })
        
        return {
            "status": 200,
            "message": "Level system information",
            "level_system": {
                "max_predefined_level": len(LEVEL_EXP_THRESHOLDS),
                "growth_factor_beyond_max": 1.3,
                "levels": level_info
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting level system info: {str(e)}")
        return {
            "status": 500,
            "message": "Có lỗi xảy ra khi lấy thông tin level system"
        }

async def simulate_learning_activity(current_user: User, db: Session) -> TestStatsResponse:
    try:
        original_level = getattr(current_user, 'level', 1)
        original_exp = getattr(current_user, 'current_exp', 0)
        original_require_exp = getattr(current_user, 'require_exp', 100)
        
        activity_exp = 100 + 100 + 50  # Course + quizzes + bonus
        new_total_exp = original_exp + activity_exp
        
        setattr(current_user, 'current_exp', new_total_exp)
        
        new_level, next_level_exp, level_increased = auto_level_up(new_total_exp, original_level)
        
        setattr(current_user, 'level', new_level)
        setattr(current_user, 'require_exp', next_level_exp)
        
        db.commit()
        
        rank_data = await calculate_user_rank(current_user, db)
        
        simulation_stats = {
            "original_level": original_level,
            "original_exp": original_exp,
            "original_require_exp": original_require_exp,
            "activity_exp_gained": activity_exp,
            "new_level": new_level,
            "new_exp": new_total_exp,
            "new_require_exp": next_level_exp,
            "level_increased": level_increased,
            "levels_gained": new_level - original_level if level_increased else 0,
            **rank_data
        }
        
        level_msg = ""
        if level_increased:
            levels_gained = new_level - original_level
            level_msg = f" 🎉 LEVEL UP! {original_level} → {new_level} (+{levels_gained} level{'s' if levels_gained > 1 else ''})"
        
        logger.info(f"Simulation completed for user {current_user.email}: {simulation_stats}")
        
        return TestStatsResponse(
            status=200,
            message=f"Mô phỏng hoạt động học tập! +{activity_exp} exp{level_msg}",
            updated_stats=simulation_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to simulate activity for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        db.rollback()
        return TestStatsResponse(
            status=500,
            message="Có lỗi xảy ra khi mô phỏng hoạt động học tập"
        )

async def add_experience(exp_amount: int, current_user: User, db: Session) -> TestStatsResponse:
    try:
        original_level = getattr(current_user, 'level', 1)
        original_exp = getattr(current_user, 'current_exp', 0)
        original_require_exp = getattr(current_user, 'require_exp', 100)
        
        new_total_exp = original_exp + exp_amount
        setattr(current_user, 'current_exp', new_total_exp)
        
        new_level, next_level_exp, level_increased = auto_level_up(new_total_exp, original_level)
        
        setattr(current_user, 'level', new_level)
        setattr(current_user, 'require_exp', next_level_exp)
        
        db.commit()
        
        rank_data = await calculate_user_rank(current_user, db)
        
        exp_gain_stats = {
            "original_level": original_level,
            "original_exp": original_exp,
            "original_require_exp": original_require_exp,
            "exp_gained": exp_amount,
            "new_level": new_level,
            "new_exp": new_total_exp,
            "new_require_exp": next_level_exp,
            "level_increased": level_increased,
            "levels_gained": new_level - original_level if level_increased else 0,
            "exp_progress_to_next": new_total_exp - get_exp_for_level(new_level),
            "exp_needed_for_next": next_level_exp - new_total_exp,
            **rank_data
        }
        
        level_msg = ""
        if level_increased:
            levels_gained = new_level - original_level
            level_msg = f" 🎉 LEVEL UP! {original_level} → {new_level}"
            if levels_gained > 1:
                level_msg += f" (+{levels_gained} levels!)"
        
        logger.info(f"Experience added for user {current_user.email}: {exp_gain_stats}")
        
        return TestStatsResponse(
            status=200,
            message=f"Thêm {exp_amount} exp thành công!{level_msg}",
            updated_stats=exp_gain_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to add experience for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        db.rollback()
        return TestStatsResponse(
            status=500,
            message="Có lỗi xảy ra khi thêm kinh nghiệm"
        )