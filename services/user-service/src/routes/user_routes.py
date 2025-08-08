from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from schemas.user_schemas import *
from controllers.user_controller import *
from services.user_service_auth import get_current_user, get_current_admin_user

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

# 2.2. Lấy avatar
@router.get("/avatar/")
async def get_user_avatar_endpoint(
    avatar_id: Optional[str] = Query(None, description="Avatar ID to retrieve"),
    user_id: Optional[str] = Query(None, description="User ID to retrieve avatar for")
):
    if not avatar_id and not user_id:
        raise HTTPException(status_code=400, detail="Either avatar_id or user_id must be provided")
    
    target_id = user_id if user_id else avatar_id
    if target_id is None:
        raise HTTPException(status_code=400, detail="No valid avatar_id or user_id provided")
    return await get_user_avatar(target_id)

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

# 2.6. Lấy thông tin nhiều users theo IDs
@router.post("/users-by-ids", response_model=dict)
async def get_users_by_ids_endpoint(
    user_ids: list[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await get_users_by_ids(user_ids, db)

# Additional utility endpoints
@router.get("/profile", response_model=UserInfoResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await get_user_info(None, current_user, db)

@router.get("/me", response_model=dict)
async def get_current_user_basic_info(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "given_name": getattr(current_user, 'given_name', None),
        "family_name": getattr(current_user, 'family_name', None),
        "level": getattr(current_user, 'level', 1),
        "avatar_url": getattr(current_user, 'avatar_url', None),
        "remind_time": getattr(current_user, 'remind_time', None)
    }

# Test APIs for development and testing
@router.put("/test/update-stats", response_model=TestStatsResponse)
async def update_test_stats_endpoint(
    request: TestStatsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
   
    return await update_test_stats(request, current_user, db)

@router.post("/test/reset-stats", response_model=TestStatsResponse)
async def reset_test_stats_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await reset_test_stats(current_user, db)

@router.get("/test/simulate-activity", response_model=TestStatsResponse)
async def simulate_learning_activity_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ..controllers.user_controller import simulate_learning_activity
    return await simulate_learning_activity(current_user, db)

@router.get("/test/level-system-info")
async def get_level_system_info_endpoint():
    from ..controllers.user_controller import get_level_system_info
    return await get_level_system_info()

@router.post("/test/add-experience", response_model=TestStatsResponse)
async def add_experience_endpoint(
    exp_amount: int = Query(..., description="Amount of experience to add", ge=1, le=10000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ..controllers.user_controller import add_experience
    return await add_experience(exp_amount, current_user, db)
