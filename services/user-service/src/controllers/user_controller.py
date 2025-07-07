import logging
from fastapi import HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from ..models import User
from ..schemas.user_schemas import *

logger = logging.getLogger(__name__)

async def change_user_info(request: ChangeInfoRequest, current_user: User, db: Session) -> MessageResponse:
    """Change user personal information"""
    try:
        logger.info(f"Changing info for user {current_user.email}")
        
        # Update user information
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
        logger.info(f"Successfully updated info for user {current_user.email}")
        
        return MessageResponse(
            status=200,
            message="Bạn đã đổi thông tin cá nhân thành công"
        )
        
    except Exception as e:
        logger.error(f"Failed to update info for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        db.rollback()
        return MessageResponse(
            status=401,
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )

async def get_user_avatar(avatar_id: str):
    """Get user avatar by avatar_id"""
    try:
        # This would typically serve the actual image file
        # For now, return error as not implemented
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy ảnh"
        )
    except Exception as e:
        logger.error(f"Error getting avatar {avatar_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy ảnh"
        )

async def update_user_avatar(avatar_file: UploadFile, current_user: User, db: Session) -> MessageResponse:
    """Update user avatar"""
    try:
        logger.info(f"Updating avatar for user {current_user.email}")
        
        # TODO: Implement file upload logic
        # For now, just return success
        
        return MessageResponse(
            status=200,
            message="Bạn đã cập nhật Avatar thành công"
        )
        
    except Exception as e:
        logger.error(f"Failed to update avatar for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        return MessageResponse(
            status=401,
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )

async def get_user_info(user_id: Optional[str], current_user: User, db: Session) -> UserInfoResponse:
    """Get user information"""
    try:
        # If user_id is provided, get that user's info (for admin or public profile)
        # Otherwise, get current user's info
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
        
        user_info = {
            "family_name": getattr(target_user, 'family_name', None),
            "given_name": getattr(target_user, 'given_name', None),
            "dob": dob_formatted,
            "avatar_id": getattr(target_user, 'avatar_url', None),
            "level": getattr(target_user, 'level', 1),
            "current_exp": getattr(target_user, 'current_exp', 0),
            "require_exp": getattr(target_user, 'require_exp', 1000),
            "sex": getattr(target_user, 'sex', None),
            "bio": getattr(target_user, 'bio', None),
            "remind_time": getattr(target_user, 'remind_time', None)
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
    """Get all users information (Admin only)"""
    try:
        users = db.query(User).filter(User.is_active == True).all()
        
        users_info = []
        for user in users:
            dob_formatted = None
            if getattr(user, 'dob', None):
                dob_formatted = getattr(user, 'dob').strftime("%d/%m/%Y")
                
            user_data = {
                "user_id": getattr(user, 'id', None),
                "family_name": getattr(user, 'family_name', None),
                "given_name": getattr(user, 'given_name', None),
                "dob": dob_formatted,
                "avatar_id": getattr(user, 'avatar_url', None),
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
    """Set study reminder time for user"""
    try:
        logger.info(f"Setting notify time for user {current_user.email}: {request.remind_time}")
        
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
    """Get dashboard information for user"""
    try:
        # Mock data for dashboard - replace with actual calculations
        dashboard_info = {
            "level": getattr(current_user, 'level', 3),
            "course_num": getattr(current_user, 'total_courses', 9),
            "quiz_num": getattr(current_user, 'total_quizzes', 19),
            "lesson_num": 238,  # This would be calculated from course service
            "finish_course_num": getattr(current_user, 'completed_courses', 3),
            "current_exp": getattr(current_user, 'current_exp', 1674767),
            "rank": 241,  # This would be calculated based on user ranking
            "user_num": db.query(User).count(),  # Total number of users
            "family_name": getattr(current_user, 'family_name', None),
            "given_name": getattr(current_user, 'given_name', None),
            "email": getattr(current_user, 'email', None),
            "average_quiz_score": getattr(current_user, 'average_score', 0.83),
            "learning_history": [],  # This would come from activity tracking
            "user_top_rank": [],  # This would be calculated from user rankings
            "remind_time": getattr(current_user, 'remind_time', None)
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
    """Save user activity milestone"""
    try:
        logger.info(f"Saving activity for user {current_user.email}")
        
        # TODO: Implement activity tracking logic
        # This would update daily activity counters
        
        return MessageResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error saving activity for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        return MessageResponse(
            status=401,
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )
