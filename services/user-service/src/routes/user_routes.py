"""
User routes for Pathlight User Service
RESTful API endpoints for user management
"""
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..database import get_db
from ..schemas.user_schemas import *
from ..controllers.user_controller import *
from ..auth import get_current_user, get_current_admin_user
from ..models import User

logger = logging.getLogger(__name__)

# Create router for user endpoints
router = APIRouter(prefix="", tags=["User Management"])

# 2.1. Đổi thông tin cá nhân
@router.put("/change-info", response_model=MessageResponse)
async def change_personal_info(
    request: ChangeInfoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user personal information"""
    logger.info(f"📝 Changing personal info for user: {current_user.email}")
    return await change_user_info(request, current_user, db)

# 2.2. Lấy avatar
@router.get("/avatar/")
async def get_user_avatar_endpoint(avatar_id: str = Query(..., description="Avatar ID to retrieve")):
    """Get user avatar by avatar_id"""
    logger.info(f"🖼️ Retrieving avatar: {avatar_id}")
    return await get_user_avatar(avatar_id)

# 2.3. Cập nhật avatar
@router.put("/avatar", response_model=MessageResponse)
async def update_avatar(
    avatar_file: UploadFile = File(..., description="Avatar image file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user avatar"""
    logger.info(f"📸 Updating avatar for user: {current_user.email}")
    return await update_user_avatar(avatar_file, current_user, db)

# 2.4. Lấy thông tin USER
@router.get("/info", response_model=UserInfoResponse)
async def get_user(
    id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user information"""
    return await get_user_info(id, current_user, db)

# 2.5. Lấy thông tin USERS (Admin only)
@router.get("/all", response_model=UsersListResponse)
async def get_users(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users information (Admin only)"""
    return await get_all_users(db)

# 2.6. Set thời gian học mỗi ngày
@router.put("/notify-time", response_model=MessageResponse)
async def set_notify_time_endpoint(
    request: NotifyTimeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set study reminder time for user"""
    return await set_notify_time(request, current_user, db)

# 2.7. Lấy thông tin cho dashboard
@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard information for user"""
    return await get_user_dashboard(current_user, db)

# 2.8. Lưu cột mốc hoạt động của USER
@router.post("/activity", response_model=MessageResponse)
async def save_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user activity milestone"""
    return await save_user_activity(current_user, db)

# Additional utility endpoints
@router.get("/profile", response_model=UserInfoResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile - shortcut endpoint"""
    logger.info(f"👤 Getting profile for current user: {current_user.email}")
    return await get_user_info(None, current_user, db)


@router.get("/me", response_model=dict)
async def get_current_user_basic_info(
    current_user: User = Depends(get_current_user)
):
    """Get basic current user information for authentication checks"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "given_name": getattr(current_user, 'given_name', None),
        "family_name": getattr(current_user, 'family_name', None),
        "level": getattr(current_user, 'level', 1),
        "avatar_url": getattr(current_user, 'avatar_url', None),
        "remind_time": getattr(current_user, 'remind_time', None)
    }
