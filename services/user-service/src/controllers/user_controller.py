import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials

from models import User, UserProfile
from services.experience_service import get_exp_for_level
from schemas.user_schemas import *
from config import config

from services.avatar_service import update_avatar as avatar_update_service, get_avatar_redirect, get_avatar_bytes
from services.admin_service import create_admin, get_admin_by_username, list_admins
from services.experience_service import (
    get_level_system_info as svc_get_level_system_info,
    update_test_stats as svc_update_test_stats,
    reset_test_stats as svc_reset_test_stats,
    simulate_learning_activity as svc_simulate_learning_activity,
    add_experience as svc_add_experience,
)
from services.activity_service import log_activity as svc_log_activity, get_activity_series as svc_get_activity_series
from services.ranking_service import calculate_user_rank, get_leaderboard_data, get_users_by_ids as svc_get_users_by_ids
from services.user_services import get_user_by_id
from services.log_service import (
    FilterKey,
    get_admin_logs as fetch_admin_logs,
    list_log_streams as fetch_log_streams,
)
from services.user_service_auth import get_current_admin_user

logger = logging.getLogger(__name__)


def _admin_guard(credentials: HTTPAuthorizationCredentials, db: Session):
    """Ensure the requester is an admin; mirror previous route-level checks."""
    try:
        get_current_admin_user(credentials, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": 503, "message": "Bạn không có quyền truy cập"},
            )
        raise
    return None


def _send_result(model_response):
    """Return JSONResponse with proper status when status != 200."""
    if isinstance(model_response, JSONResponse):
        return model_response
    status_code = getattr(model_response, "status", 200)
    if status_code != 200 and hasattr(model_response, "dict"):
        return JSONResponse(status_code=status_code, content=model_response.dict())
    return model_response

# ---------- Profile & Basic Info ----------
async def change_user_info(request: ChangeInfoRequest, current_user: User, db: Session) -> MessageResponse:
    try:
        profile = getattr(current_user, 'profile', None)
        if not profile:
            profile = UserProfile(
                profile_id=str(uuid.uuid4()),
                subscription=0,
                streak=0,
                level=1,
                current_exp=0,
                require_exp=get_exp_for_level(2),
            )
            db.add(profile)
            setattr(current_user, 'profile', profile)
            if not getattr(current_user, 'profile_id', None):
                setattr(current_user, 'profile_id', profile.profile_id)

        for field in ["family_name", "given_name", "dob", "sex", "bio"]:
            value = getattr(request, field, None)
            if value is not None:
                setattr(profile, field, value)
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


async def get_user_avatar_stream(user_id: Optional[str], db: Session) -> Response:
    if not user_id:
        raise HTTPException(status_code=400, detail="Thiếu user-id")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    def _gender_defaults(user: User) -> list[str]:
        raw_sex = getattr(user, 'sex', None)
        sex = str(raw_sex).lower() if raw_sex is not None else ''
        is_female = sex.startswith('f') or sex in {'nu', 'female', 'girl', 'woman'}
        base = 'female' if is_female else 'male'
        return [
            f"{base}.png",
            f"avatars/{base}.png",
            f"default/{base}.png",
            f"avatars/default/{base}.png",
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
        avatar_url = f"{config.BASE_URL}/user/avatar?user-id={target_user.id}" if avatar_id else None
        
        # Calculate rank
        rank_data = calculate_user_rank(target_user, db)
        
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
            "require_exp": getattr(target_user, 'require_exp', None) or get_exp_for_level((getattr(target_user, 'level', 1) or 1) + 1),
            "subscription": getattr(target_user, 'subscription', 0),
            "streak": getattr(target_user, 'streak', 0),
            "sex": getattr(target_user, 'sex', None),
            "bio": getattr(target_user, 'bio', None),
            "remind_time": getattr(target_user, 'remind_time', None),
            "created_at": getattr(target_user, 'created_at', None),
            "rank": rank_data.get("rank"),
            "total_users": rank_data.get("total_users")
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


async def get_admin_user_overview(credentials: HTTPAuthorizationCredentials, db: Session) -> AdminUsersResponse | JSONResponse:
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        # Fetch users with profiles via join to get accurate data
        users = db.query(User).filter(User.is_active == True).all()  # noqa: E712
        user_items = []
        for user in users:
            # Get actual values from profile, don't use defaults
            profile = getattr(user, 'profile', None)
            user_items.append(
                AdminUserItem(
                    user_id=str(user.id),
                    email=getattr(user, 'email', None),
                    given_name=getattr(user, 'given_name', None),
                    family_name=getattr(user, 'family_name', None),
                    level=getattr(profile, 'level', None) if profile else None,
                    current_exp=getattr(profile, 'current_exp', None) if profile else None,
                    subscription=getattr(profile, 'subscription', None) if profile else None,
                )
            )
        return AdminUsersResponse(status=200, users=user_items)
    except Exception as e:  # pragma: no cover
        logger.error(f"Error retrieving admin user overview: {e}")
        return AdminUsersResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại")


async def create_admin_account(request: AdminCreateRequest, credentials: HTTPAuthorizationCredentials, db: Session) -> MessageResponse | JSONResponse:
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        username = request.username.strip()
        if not username:
            return _send_result(MessageResponse(status=400, message="Username không được để trống"))
        if get_admin_by_username(db, username):
            return _send_result(MessageResponse(status=400, message="Tên đăng nhập đã tồn tại"))
        try:
            create_admin(db, username, request.password)
        except Exception as exc:
            return _send_result(MessageResponse(status=500, message="Không thể tạo admin mới"))
        return _send_result(MessageResponse(status=200, message="Admin đã được tạo thành công"))
    except Exception as e:  # pragma: no cover
        logger.error(f"Unexpected error during admin creation: {e}")
        return _send_result(MessageResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại"))


async def admin_update_subscription(user_id: str, request: AdminUpdateSubscriptionRequest, credentials: HTTPAuthorizationCredentials, db: Session) -> MessageResponse | JSONResponse:
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        target_user = get_user_by_id(db, user_id)
        if not target_user:
            return _send_result(MessageResponse(status=404, message="Không tìm thấy người dùng"))

        profile = getattr(target_user, 'profile', None)
        if not profile:
            profile = UserProfile(
                profile_id=str(uuid.uuid4()),
                subscription=0,
                streak=0,
                level=1,
                current_exp=0,
                require_exp=get_exp_for_level(2),
            )
            db.add(profile)
            setattr(target_user, 'profile', profile)
            if not getattr(target_user, 'profile_id', None):
                setattr(target_user, 'profile_id', profile.profile_id)
        setattr(target_user, 'subscription', request.subscription)
        db.flush()
        db.commit()
        
        db.expire_all()
        verified_user = get_user_by_id(db, user_id)
        verified_sub = getattr(verified_user, 'subscription', None)
        if verified_sub != request.subscription:
            logger.error(f"Subscription update failed: expected {request.subscription}, got {verified_sub}")
            return MessageResponse(status=500, message=f"Lỗi: Gói không được lưu (hiện tại: {verified_sub})")
        return MessageResponse(status=200, message=f"Đã cập nhật gói thuê bao thành {verified_sub}")
    except Exception as e:
        logger.error(f"Failed to update subscription for user {user_id}: {e}")
        db.rollback()
        return MessageResponse(status=500, message="Không thể cập nhật gói thuê bao")


async def admin_add_experience_for_user(user_id: str, request: AdminExperienceRequest, credentials: HTTPAuthorizationCredentials, db: Session) -> TestStatsResponse | JSONResponse:
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        target_user = get_user_by_id(db, user_id)
        if not target_user:
            return _send_result(TestStatsResponse(status=404, message="Không tìm thấy người dùng"))

        profile = getattr(target_user, 'profile', None)
        if not profile:
            profile = UserProfile(
                profile_id=str(uuid.uuid4()),
                subscription=0,
                streak=0,
                level=1,
                current_exp=0,
                require_exp=get_exp_for_level(2),
            )
            db.add(profile)
            setattr(target_user, 'profile', profile)
            if not getattr(target_user, 'profile_id', None):
                setattr(target_user, 'profile_id', profile.profile_id)
            db.commit()

        return await svc_add_experience(request.exp, target_user, db)
    except Exception as e:
        logger.error(f"Failed to add exp for user {user_id}: {e}", exc_info=True)
        db.rollback()
        return TestStatsResponse(status=500, message="Không thể thêm exp cho người dùng")


async def admin_adjust_experience_step(user_id: str, request: AdminExperienceDeltaRequest, credentials: HTTPAuthorizationCredentials, db: Session) -> TestStatsResponse | JSONResponse:
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        target_user = get_user_by_id(db, user_id)
        if not target_user:
            return _send_result(TestStatsResponse(status=404, message="Không tìm thấy người dùng"))

        profile = getattr(target_user, 'profile', None)
        if not profile:
            profile = UserProfile(
                profile_id=str(uuid.uuid4()),
                subscription=0,
                streak=0,
                level=1,
                current_exp=0,
                require_exp=get_exp_for_level(2),
            )
            db.add(profile)
            setattr(target_user, 'profile', profile)
            if not getattr(target_user, 'profile_id', None):
                setattr(target_user, 'profile_id', profile.profile_id)
            db.commit()
        result = await svc_add_experience(request.delta, target_user, db)
        return result
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to adjust exp for user {user_id}: {e}", exc_info=True)
        db.rollback()
        return TestStatsResponse(status=500, message="Không thể điều chỉnh exp cho người dùng", updated_stats=None)


async def list_admin_accounts(credentials: HTTPAuthorizationCredentials, db: Session) -> AdminListResponse | JSONResponse:
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        admins = list_admins(db)
        admin_items = []
        for a in admins:
            created_at_val = getattr(a, 'created_at', None)
            created_at = created_at_val.isoformat() if created_at_val else None
            admin_items.append(
                AdminItem(
                    id=str(getattr(a, 'id', '')),
                    username=str(getattr(a, 'username', '')),
                    created_at=created_at,
                )
            )
        return AdminListResponse(status=200, admins=admin_items)
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to list admins: {e}")
        return AdminListResponse(status=500, message="Không thể lấy danh sách admin")

# ---------- Settings ----------
async def set_notify_time(request: NotifyTimeRequest, current_user: User, db: Session) -> MessageResponse:
    try:
        parsed_time = datetime.strptime(request.remind_time, "%H:%M").time()
        now = datetime.now(timezone.utc)
        remind_dt = datetime.combine(now.date(), parsed_time, tzinfo=timezone.utc)

        profile = getattr(current_user, 'profile', None)
        if not profile:
            profile = UserProfile(
                profile_id=str(uuid.uuid4()),
                subscription=0,
                streak=0,
                level=1,
                current_exp=0,
                require_exp=get_exp_for_level(2),
            )
            db.add(profile)
            setattr(current_user, 'profile', profile)
            if not getattr(current_user, 'profile_id', None):
                setattr(current_user, 'profile_id', profile.profile_id)

        setattr(profile, 'remind_time', remind_dt)
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
        avatar_url = (
            f"{config.BASE_URL}/user/avatar?user-id={current_user.id}" if avatar_id else None
        )
        dob_value = getattr(current_user, 'dob', None)
        dob_formatted = dob_value.strftime("%d/%m/%Y") if dob_value else None
        rank_data = calculate_user_rank(current_user, db)
        leaderboard = get_leaderboard_data(db)
        
        # Calculate current streak
        from services.activity_service import get_current_streak
        current_streak = get_current_streak(str(current_user.id), db)
        
        dashboard_info = {
            "id": current_user.id,
            "email": current_user.email,
            "level": getattr(current_user, 'level', 1),
            "current_exp": getattr(current_user, 'current_exp', 0),
            "require_exp": getattr(current_user, 'require_exp', 100),
            "family_name": getattr(current_user, 'family_name', None),
            "given_name": getattr(current_user, 'given_name', None),
            "birth_date": dob_formatted,
            "avatar_id": avatar_id,
            "avatar_url": avatar_url,
            "remind_time": getattr(current_user, 'remind_time', None),
            "bio": getattr(current_user, 'bio', None),
            "sex": getattr(current_user, 'sex', None),
            "streak": current_streak,
            # Ranking
            "rank": rank_data["rank"],
            "total_users": rank_data["total_users"],
            "subscription": getattr(current_user, 'subscription', 0),
            "created_at": getattr(current_user, 'created_at', None),
            "user_top_rank": leaderboard,
        }
        return DashboardResponse(status=200, info=dashboard_info)
    except Exception as e:  # pragma: no cover
        logger.error(f"Dashboard error for {getattr(current_user, 'email', 'unknown')}: {e}")
        return DashboardResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại")


# ---------- Experience ----------
async def add_experience(request: ExperienceAddRequest, current_user: User, db: Session) -> TestStatsResponse:
    try:
        target_user = db.query(User).filter(User.id == getattr(current_user, 'id')).first()
        if not target_user:
            # Fallback to the provided current_user if not found in this session
            target_user = current_user
        result = await svc_add_experience(request.exp, target_user, db)
        logger.info("controllers.add_experience result for user %s: %s", getattr(target_user, 'email', getattr(target_user, 'id', 'unknown')), getattr(result, 'updated_stats', None))
        return result
    except Exception as e:
        logger.error(f"add_experience controller error: {e}")
        raise

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


# ---------- Activity tracking ----------
async def log_learning_activity(request: ActivityLogRequest, current_user: User, db: Session):
    # Ensure we operate on a User instance attached to this DB session
    target_user = db.query(User).filter(User.id == getattr(current_user, 'id')).first()
    if not target_user:
        target_user = current_user
    return svc_log_activity(request, target_user, db)


async def get_learning_activity(current_user: User, db: Session, days: int = 365):
    return svc_get_activity_series(current_user, db, days)

# ---------- Admin Update Email ----------
async def admin_update_user_email(user_id: str, new_email: str, credentials: HTTPAuthorizationCredentials, db: Session) -> MessageResponse | JSONResponse:
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            return _send_result(MessageResponse(status=404, message="Người dùng không tồn tại"))

        existing_user = db.query(User).filter(User.email == new_email).first()
        if existing_user and str(getattr(existing_user, 'id')) != str(user_id):
            return _send_result(MessageResponse(status=500, message="Email muốn thay đổi đã tồn tại trong hệ thống, vui lòng cung cấp email khác"))

        setattr(target_user, 'email', new_email)
        db.commit()
        logger.info(f"Admin updated email for user {user_id} to {new_email}")
        return _send_result(MessageResponse(status=200, message="Cập nhật email thành công"))
    except Exception as e:
        logger.error(f"Admin update email error: {e}")
        db.rollback()
        return _send_result(MessageResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại"))

# ---------- Admin Delete User ----------
async def admin_delete_user(user_id: str, credentials: HTTPAuthorizationCredentials, db: Session) -> MessageResponse | JSONResponse:
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        from jose import jwt
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            return _send_result(MessageResponse(status=404, message="Người dùng không tồn tại"))
        
        # Get admin email for audit logging
        token = credentials.credentials
        decoded = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        admin_email = decoded.get("email", "admin")
        
        # Delete all courses owned by the user (cascade delete)
        try:
            from services.external.course_client import delete_user_courses
            courses_deleted = delete_user_courses(user_id, admin_email)
            if not courses_deleted:
                logger.warning(f"Failed to delete courses for user {user_id}, continuing with user deletion")
            else:
                logger.info(f"Successfully deleted all courses for user {user_id}")
        except Exception as course_delete_error:
            logger.error(f"Error deleting courses for user {user_id}: {course_delete_error}")
            logger.warning(f"Continuing with user deletion despite course deletion error")
        
        # Delete user profile and account
        profile = getattr(target_user, 'profile', None)
        if profile:
            db.delete(profile)
        
        db.delete(target_user)
        db.commit()
        logger.info(f"Admin deleted user {user_id} and profile")
        return _send_result(MessageResponse(status=200, message="Xóa người dùng thành công"))
    except Exception as e:  # pragma: no cover
        logger.error(f"Admin delete user error: {e}")
        db.rollback()
        return _send_result(MessageResponse(status=500, message="Có lỗi xảy ra, xin vui lòng thử lại"))

# ---------- Admin Get AWS Costs ----------
async def get_admin_aws_costs(credentials: HTTPAuthorizationCredentials, db: Session):
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    from services.aws_cost_service import get_aws_costs_last_30_days
    return get_aws_costs_last_30_days()


async def get_admin_logs(
    filter_key: FilterKey,
    service: Optional[str],
    log_stream: Optional[str],
    level: Optional[str],
    credentials: HTTPAuthorizationCredentials,
    db: Session,
):
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    try:
        result = fetch_admin_logs(filter_key, service=service, log_stream=log_stream, level_filter=level)
        return result
    except Exception as e:
        return AdminLogsResponse(status=500, message="Lỗi khi lấy logs", logs=[])


async def get_admin_log_streams(
    filter_key: FilterKey,
    service: Optional[str],
    credentials: HTTPAuthorizationCredentials,
    db: Session,
):
    guard = _admin_guard(credentials, db)
    if guard:
        return guard
    return fetch_log_streams(filter_key, service=service)
