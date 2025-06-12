from datetime import timedelta
from jose import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import create_access_token, verify_password
from ..core.settings import get_settings
from ..crud.user import create_user, get_user_by_email, get_user_by_id
from ..schemas.user import UserCreate, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(db, **user_in.model_dump())
    settings = get_settings()
    access = create_access_token({"sub": str(user.user_id)}, timedelta(minutes=settings.access_token_expire_minutes))
    refresh = create_access_token({"sub": str(user.user_id)}, timedelta(days=settings.refresh_token_expire_days))
    return Token(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    settings = get_settings()
    access = create_access_token({"sub": str(user.user_id)}, timedelta(minutes=settings.access_token_expire_minutes))
    refresh = create_access_token({"sub": str(user.user_id)}, timedelta(days=settings.refresh_token_expire_days))
    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token)
async def refresh(token: Token, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    payload = jwt.decode(token.refresh_token, settings.secret_key, algorithms=["HS256"])
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token({"sub": str(user.user_id)}, timedelta(minutes=settings.access_token_expire_minutes))
    refresh_new = create_access_token({"sub": str(user.user_id)}, timedelta(days=settings.refresh_token_expire_days))
    return Token(access_token=access, refresh_token=refresh_new)

@router.post("/admin/login", response_model=Token)
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    from ..models.user import Admin
    from sqlalchemy import select
    res = await db.execute(select(Admin).where(Admin.username == form_data.username))
    admin = res.scalars().first()
    if not admin or not verify_password(form_data.password, admin.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    settings = get_settings()
    access = create_access_token({"sub": str(admin.admin_id), "role": "admin"}, timedelta(minutes=settings.access_token_expire_minutes))
    refresh = create_access_token({"sub": str(admin.admin_id), "role": "admin"}, timedelta(days=settings.refresh_token_expire_days))
    return Token(access_token=access, refresh_token=refresh)
