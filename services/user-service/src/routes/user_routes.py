from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal
import logging

from fastapi.security import HTTPAuthorizationCredentials

from database import get_db
from schemas.user_schemas import (
    MessageResponse,
    ChangeInfoRequest,
    UserInfoResponse,
    NotifyTimeRequest,
    DashboardResponse,
    AdminUsersResponse,
    AdminCreateRequest,
    AdminUpdateEmailRequest,
    AdminCostResponse,
    AdminLogsResponse,
    ExperienceAddRequest,
    TestStatsResponse,
    ActivityLogRequest,
)
from models import User
from controllers.user_controller import (
    change_user_info,
    update_user_avatar,
    get_user_avatar_stream,
    get_user_info,
    get_admin_user_overview,
    create_admin_account,
    set_notify_time,
    get_user_dashboard,
    save_user_activity,
    admin_update_user_email,
    admin_delete_user,
    get_admin_aws_costs,
    get_admin_logs,
    add_experience,
    log_learning_activity,
    get_learning_activity,
)
from services.user_service_auth import get_current_user, get_current_admin_user, security

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
@router.get("/avatar")
async def get_avatar(
    user_id: Optional[str] = Query(None, alias="user-id", description="User ID muốn lấy avatar"),
    db: Session = Depends(get_db)
):
    return await get_user_avatar_stream(user_id, db)

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
@router.get("/admin/users", response_model=AdminUsersResponse)
async def get_users_for_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    return await get_admin_user_overview(credentials, db)


@router.post("/admin/create", response_model=MessageResponse)
async def create_admin_user(
    request: AdminCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    return await create_admin_account(request, credentials, db)

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


@router.post("/experience/add", response_model=TestStatsResponse)
async def add_experience_endpoint(
    request: ExperienceAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await add_experience(request, current_user, db)

# 2.8. Lưu cột mốc hoạt động của USER
@router.post("/activity")
async def save_activity(
    request: ActivityLogRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await log_learning_activity(request, current_user, db)


@router.get("/activity")
async def list_activity(
    days: int = Query(365, ge=1, le=1095),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await get_learning_activity(current_user, db, days)

# 6.5. Admin update user email
@router.put("/admin/user", response_model=MessageResponse)
async def admin_update_email(
    request: AdminUpdateEmailRequest,
    user_id: str = Query(..., alias="userid"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    return await admin_update_user_email(user_id, request.email, credentials, db)

# 6.6. Admin delete user
@router.delete("/admin/user", response_model=MessageResponse)
async def admin_delete_user_endpoint(
    user_id: str = Query(..., alias="userid"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    return await admin_delete_user(user_id, credentials, db)

# 6.3. Admin get AWS costs
@router.get("/admin/cost", response_model=AdminCostResponse)
async def admin_get_costs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    return await get_admin_aws_costs(credentials, db)

# 6.3. Admin get AWS CloudWatch logs
@router.get("/admin/log", response_model=AdminLogsResponse)
async def get_admin_logs_endpoint(
    filter_key: Literal["daily", "weekly", "monthly", "hourly", "30m", "1m"] = Query(
        "daily", pattern="^(daily|weekly|monthly|hourly|30m|1m)$"
    ),
    service: Optional[str] = Query(None, description="Tên log group hoặc suffix service"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    return await get_admin_logs(filter_key, service, credentials, db)
