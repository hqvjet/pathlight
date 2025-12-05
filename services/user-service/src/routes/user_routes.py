from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

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
)
from models import User
from controllers.user_controller import (
    change_user_info,
    update_user_avatar,
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
)
from services.user_service_auth import get_current_user, get_current_admin_user, security
from services.avatar_service import get_avatar_bytes  # bytes version

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
    user_id: Optional[str] = Query(None, alias="user-id", description="User ID muốn lấy avatar"),
    db: Session = Depends(get_db)
):
    if not user_id:
        raise HTTPException(status_code=400, detail="Thiếu user-id")
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    def _gender_defaults(user: User) -> list[str]:
        sex = (getattr(user, 'sex', '') or '').lower()
        is_female = sex.startswith('f') or sex in {'nu', 'female', 'girl', 'woman'}
        base = 'female' if is_female else 'male'
        return [
            f"{base}.png",
            f"avatars/{base}.png",
            f"default/{base}.png",
            f"avatars/default/{base}.png"
        ]

    candidates: list[str] = []
    avatar_url_val = getattr(target_user, 'avatar_url', None)
    if avatar_url_val:
        candidates.append(avatar_url_val)
        if '/' not in avatar_url_val and not avatar_url_val.lower().endswith(('.png', '.jpg', '.jpeg')):
            candidates.append(f"avatars/{avatar_url_val}.jpg")
            candidates.append(f"avatars/{avatar_url_val}")
    else:
        candidates.extend(_gender_defaults(target_user))
    for d in _gender_defaults(target_user):
        if d not in candidates:
            candidates.append(d)

    last_error: Optional[HTTPException] = None
    for key in candidates:
        try:
            content, media_type, headers = get_avatar_bytes(key)
            return Response(content=content, media_type=media_type, headers=headers)
        except HTTPException as e:
            if e.status_code != 404:
                raise
            last_error = e
            continue
    if last_error:
        raise last_error
    raise HTTPException(status_code=404, detail="Avatar không tồn tại")

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
    try:
        get_current_admin_user(credentials, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": 503, "message": "Bạn không có quyền truy cập"}
            )
        raise
    result = await get_admin_user_overview(db)
    return result


@router.post("/admin/create", response_model=MessageResponse)
async def create_admin_user(
    request: AdminCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        get_current_admin_user(credentials, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": 503, "message": "Bạn không có quyền truy cập"}
            )
        raise

    result = await create_admin_account(request, db)
    if result.status == 200:
        return result
    status_code = 400 if result.status == 400 else 500
    return JSONResponse(status_code=status_code, content=result.dict())

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

# 6.5. Admin update user email
@router.put("/admin/user", response_model=MessageResponse)
async def admin_update_email(
    request: AdminUpdateEmailRequest,
    user_id: str = Query(..., alias="userid"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        get_current_admin_user(credentials, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": 503, "message": "Bạn không có quyền truy cập"}
            )
        raise
    
    result = await admin_update_user_email(user_id, request.email, db)
    if result.status == 200:
        return result
    status_code = 404 if result.status == 404 else 500
    return JSONResponse(status_code=status_code, content=result.dict())

# 6.6. Admin delete user
@router.delete("/admin/user", response_model=MessageResponse)
async def admin_delete_user_endpoint(
    user_id: str = Query(..., alias="userid"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        get_current_admin_user(credentials, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": 503, "message": "Bạn không có quyền truy cập"}
            )
        raise
    
    result = await admin_delete_user(user_id, db)
    if result.status == 200:
        return result
    status_code = 404 if result.status == 404 else 500
    return JSONResponse(status_code=status_code, content=result.dict())

# 6.3. Admin get AWS costs
@router.get("/admin/cost", response_model=AdminCostResponse)
async def admin_get_costs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        get_current_admin_user(credentials, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": 503, "message": "Bạn không có quyền truy cập"}
            )
        raise

    result = await get_admin_aws_costs()
    return result

# 6.3. Admin get AWS CloudWatch logs
@router.get("/admin/log", response_model=AdminLogsResponse)
async def get_admin_logs_endpoint(
    filter: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        get_current_admin_user(credentials, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": 503, "message": "Bạn không có quyền truy cập"}
            )
        raise

    result = get_admin_logs(filter)
    if result.status == 200:
        return result
    status_code = 400 if result.status == 400 else 502 if result.status == 502 else 500
    return JSONResponse(status_code=status_code, content=result.dict())
