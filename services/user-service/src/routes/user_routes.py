from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from schemas.user_schemas import (
    MessageResponse,
    ChangeInfoRequest,
    UserInfoResponse,
    UsersListResponse,
    NotifyTimeRequest,
    DashboardResponse,
)
from models import User
from controllers.user_controller import (
    change_user_info,
    update_user_avatar,
    get_user_info,
    get_all_users,
    set_notify_time,
    get_user_dashboard,
    save_user_activity,
)
from services.user_service_auth import get_current_user, get_current_admin_user
from services.avatar_service import get_avatar_stream  # streaming avatar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["User Management"])

# 2.1. Đổi thông tin cá nhân
@router.put("/change-info", response_model=MessageResponse)
async def change_personal_info(
    request: ChangeInfoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await change_user_info(request, current_user, db)

# 2.2. Lấy avatar (stream trực tiếp)
@router.get("/avatar")
async def get_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fallback theo giới tính nếu chưa có hoặc ảnh bị missing
    def _gender_default():
        sex = (current_user.sex or '').lower()
        if sex.startswith('f') or sex in {'nu', 'female', 'girl', 'woman'}:
            return 'female.png'
        return 'male.png'
    primary_key = current_user.avatar_url or _gender_default()
    try:
        return get_avatar_stream(primary_key)
    except HTTPException as e:
        if e.status_code == 404:
            fallback_key = _gender_default()
            if fallback_key != primary_key:
                return get_avatar_stream(fallback_key)
        raise

# 2.3. Cập nhật avatar
@router.put("/avatar", response_model=MessageResponse)
async def update_avatar(
    avatar_file: UploadFile = File(..., description="Avatar image file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await update_user_avatar(avatar_file, current_user, db)

# 2.4. Lấy thông tin USER
@router.get("/info", response_model=UserInfoResponse)
async def get_user(
    id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await get_user_info(id, current_user, db)

# 2.5. Lấy thông tin USERS (Admin only)
@router.get("/all", response_model=UsersListResponse)
async def get_users(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    return await get_all_users(db)

# 2.6. Set thời gian học mỗi ngày
@router.put("/notify-time", response_model=MessageResponse)
async def set_notify_time_endpoint(
    request: NotifyTimeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await set_notify_time(request, current_user, db)

# 2.7. Lấy thông tin cho dashboard
@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await get_user_dashboard(current_user, db)

# 2.8. Lưu cột mốc hoạt động của USER
@router.post("/activity", response_model=MessageResponse)
async def save_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await save_user_activity(current_user, db)
