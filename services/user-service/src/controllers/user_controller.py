import logging
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import UploadFile

from models import User
from schemas.user_schemas import *  # noqa
from config import config

from services.avatar_service import update_avatar as avatar_update_service, get_avatar_redirect
from services.admin_service import create_admin, get_admin_by_username
from services.experience_service import (
    get_level_system_info as svc_get_level_system_info,
    update_test_stats as svc_update_test_stats,
    reset_test_stats as svc_reset_test_stats,
    simulate_learning_activity as svc_simulate_learning_activity,
    add_experience as svc_add_experience,
)
from services.ranking_service import calculate_user_rank, get_leaderboard_data, get_users_by_ids as svc_get_users_by_ids
from services.external.course_client import get_course_stats
from services.external.quiz_client import get_quiz_stats

logger = logging.getLogger(__name__)

# ---------- Profile & Basic Info ----------
async def change_user_info(request: ChangeInfoRequest, current_user: User, db: Session) -> MessageResponse:
    try:
        for field in ["family_name", "given_name", "dob", "sex", "bio"]:
            value = getattr(request, field, None)
            if value is not None:
                setattr(current_user, field, value)
        db.commit()
        logger.info(f"User info updated: {current_user.email}")
        return MessageResponse(status=200, message="Bạn đã đổi thông tin cá nhân thành công")
    except Exception as e:  # pragma: no cover
        logger.error(f"Update info failed: {getattr(current_user, 'email', 'unknown')}: {e}")
        db.rollback()
        return MessageResponse(status=401, message="Có lỗi xảy ra, xin vui lòng thử lại")

# ---------- Avatar ----------
async def get_user_avatar(avatar_id: str):
    return get_avatar_redirect(avatar_id)

async def update_user_avatar(avatar_file: UploadFile, current_user: User, db: Session) -> MessageResponse:
    status_code, msg = avatar_update_service(avatar_file, current_user, db)
    return MessageResponse(status=status_code, message=msg)

# ---------- User Info Retrieval ----------
async def get_user_info(user_id: Optional[str], current_user: User, db: Session) -> UserInfoResponse:
    try:
        target_user = current_user
        if user_id:
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                return UserInfoResponse(status=401, message="Người dùng không tồn tại")
        dob_value = getattr(target_user, 'dob', None)
        dob_formatted = dob_value.strftime("%d/%m/%Y") if dob_value else None
        avatar_id = getattr(target_user, 'avatar_url', None)
        # Unified avatar_url format with user-id query param (same as dashboard)
        avatar_url = f"{config.BASE_URL}/user/avatar?user-id={target_user.id}" if avatar_id else None
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
        return UserInfoResponse(status=200, Info=user_info)
    except Exception as e:  # pragma: no cover
        logger.error(f"Error getting user info: {e}")
        return UserInfoResponse(status=401, message="Có lỗi xảy ra, xin vui lòng thử lại")

async def get_all_users(db: Session) -> UsersListResponse:
    try:
        users = db.query(User).filter(User.is_active == True).all()  # noqa: E712
        infos = []
        for u in users:
            dob_value = getattr(u, 'dob', None)
            dob_formatted = dob_value.strftime("%d/%m/%Y") if dob_value else None
            avatar_id = getattr(u, 'avatar_url', None)
            avatar_url = None
            if avatar_id:
                avatar_url = avatar_id if avatar_id.startswith('http') else f"{config.BASE_URL}/user/avatar"
            infos.append({
                "user_id": getattr(u, 'id', None),
                "family_name": getattr(u, 'family_name', None),
                "given_name": getattr(u, 'given_name', None),
                "dob": dob_formatted,
                "avatar_id": avatar_id,
                "avatar_url": avatar_url,
                "level": getattr(u, 'level', 1),
                "current_exp": getattr(u, 'current_exp', 0),
                "require_exp": getattr(u, 'require_exp', 1000),
                "sex": getattr(u, 'sex', None),
                "bio": getattr(u, 'bio', None),
                "remind_time": getattr(u, 'remind_time', None)
            })
        return UsersListResponse(status=200, infos=infos)
    except Exception as e:  # pragma: no cover
        logger.error(f"Error getting all users: {e}")
        return UsersListResponse(status=401, message="Có lỗi xảy ra, xin vui lòng thử lại")


async def get_admin_user_overview(db: Session) -> AdminUsersResponse:
    """Return compact user data for admin dashboard listing"""
    try:
        users = db.query(User).all()
        user_items = [
            AdminUserItem(
                user_id=str(user.id),
                email=getattr(user, 'email', None),
                given_name=getattr(user, 'given_name', None),
                level=getattr(user, 'level', None),
            )
            for user in users
        ]
        return AdminUsersResponse(status=200, users=user_items)
    except Exception as e:  # pragma: no cover
        logger.error(f"Error retrieving admin user overview: {e}")
        return AdminUsersResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại")


async def create_admin_account(request: AdminCreateRequest, db: Session) -> MessageResponse:
    try:
        username = request.username.strip()
        if not username:
            return MessageResponse(status=400, message="Username không được để trống")
        if get_admin_by_username(db, username):
            return MessageResponse(status=400, message="Tên đăng nhập đã tồn tại")
        try:
            create_admin(db, username, request.password)
        except Exception as exc:
            logger.error(f"Failed to create admin '{username}': {exc}")
            return MessageResponse(status=500, message="Không thể tạo admin mới")
        return MessageResponse(status=200, message="Admin đã được tạo thành công")
    except Exception as e:  # pragma: no cover
        logger.error(f"Unexpected error during admin creation: {e}")
        return MessageResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại")

# ---------- Settings ----------
async def set_notify_time(request: NotifyTimeRequest, current_user: User, db: Session) -> MessageResponse:
    try:
        setattr(current_user, 'remind_time', request.remind_time)
        db.commit()
        logger.info(f"Set remind time for {current_user.email} -> {request.remind_time}")
        return MessageResponse(status=200, message="Đã đặt lịch thành công")
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to set remind time for {getattr(current_user, 'email', 'unknown')}: {e}")
        db.rollback()
        return MessageResponse(status=401, message="Có lỗi xảy ra, xin vui lòng thử lại")

# ---------- Dashboard ----------
async def get_user_dashboard(current_user: User, db: Session) -> DashboardResponse:
    try:
        avatar_id = getattr(current_user, 'avatar_url', None)
        # Always provide endpoint with user-id query param when user has (or may have) an avatar.
        avatar_url = (
            f"{config.BASE_URL}/user/avatar?user-id={current_user.id}" if avatar_id else None
        )
        course_stats = get_course_stats(str(getattr(current_user, 'email', '')))
        quiz_stats = get_quiz_stats(str(getattr(current_user, 'email', '')))
        rank_data = calculate_user_rank(current_user, db)
        leaderboard = get_leaderboard_data(db)
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
            # Course
            "course_num": course_stats["total_courses"],
            "total_courses": course_stats["total_courses"],
            "finish_course_num": course_stats["completed_courses"],
            "completed_courses": course_stats["completed_courses"],
            "lesson_num": course_stats["total_lessons"],
            # Quiz
            "quiz_num": quiz_stats["total_quizzes"],
            "total_quizzes": quiz_stats["total_quizzes"],
            "completed_quizzes": quiz_stats["completed_quizzes"],
            "average_quiz_score": quiz_stats["average_score"],
            "average_score": quiz_stats["average_score"],
            # Rank
            "rank": rank_data["rank"],
            "user_num": rank_data["total_users"],
            # Leaderboard
            "user_top_rank": leaderboard,
            # Placeholder
            "learning_history": [],
        }
        return DashboardResponse(status=200, info=dashboard_info)
    except Exception as e:  # pragma: no cover
        logger.error(f"Dashboard error for {getattr(current_user, 'email', 'unknown')}: {e}")
        return DashboardResponse(status=401, message="Có lỗi xảy ra, xin vui lòng thử lại")

# ---------- Activity (placeholder) ----------
async def save_user_activity(current_user: User, db: Session) -> MessageResponse:
    return MessageResponse(status=200)

# ---------- Ranking wrappers (backward compatibility) ----------
async def get_users_by_ids(user_ids: list[str], db: Session) -> dict:
    return svc_get_users_by_ids(user_ids, db)

# ---------- Experience wrappers ----------
async def update_test_stats(request: TestStatsRequest, current_user: User, db: Session) -> TestStatsResponse:
    return await svc_update_test_stats(request, current_user, db)

async def reset_test_stats(current_user: User, db: Session) -> TestStatsResponse:
    return await svc_reset_test_stats(current_user, db)

async def get_level_system_info() -> dict:
    return await svc_get_level_system_info()

async def simulate_learning_activity(current_user: User, db: Session) -> TestStatsResponse:
    return await svc_simulate_learning_activity(current_user, db)

async def add_experience(exp_amount: int, current_user: User, db: Session) -> TestStatsResponse:
    return await svc_add_experience(exp_amount, current_user, db)

# ---------- Admin Update Email ----------
async def admin_update_user_email(user_id: str, new_email: str, db: Session) -> MessageResponse:
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            return MessageResponse(status=404, message="Người dùng không tồn tại")
        
        existing_user = db.query(User).filter(User.email == new_email).first()
        if existing_user:
            if str(getattr(existing_user, 'id')) != str(user_id):
                return MessageResponse(status=500, message="Email muốn thay đổi đã tồn tại trong hệ thống, vui lòng cung cấp email khác")
        
        setattr(target_user, 'email', new_email)
        db.commit()
        logger.info(f"Admin updated email for user {user_id} to {new_email}")
        return MessageResponse(status=200, message="Cập nhật email thành công")
    except Exception as e:
        logger.error(f"Admin update email error: {e}")
        db.rollback()
        return MessageResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại")

# ---------- Admin Delete User ----------
async def admin_delete_user(user_id: str, db: Session) -> MessageResponse:
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            return MessageResponse(status=404, message="Người dùng không tồn tại")
        
        # Delete user and all related resources
        db.delete(target_user)
        db.commit()
        logger.info(f"Admin deleted user {user_id} and all related resources")
        return MessageResponse(status=200, message="Xóa người dùng thành công")
    except Exception as e:  # pragma: no cover
        logger.error(f"Admin delete user error: {e}")
        db.rollback()
        return MessageResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại")

# ---------- Admin Get AWS Costs ----------
async def get_admin_aws_costs():
    from services.aws_cost_service import get_aws_costs_last_30_days
    return get_aws_costs_last_30_days()