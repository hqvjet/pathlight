from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth_schemas import *
from controllers.auth_controller import *

router = APIRouter(prefix="", tags=["Authentication"])

# 1.1. Đăng ký
@router.post("/signup", response_model=MessageResponse)
async def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    """User registration endpoint"""
    return await signup_user(user_data, db)

# 1.2. Xác thực Email
@router.get("/verify-email", response_model=AuthResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email endpoint"""
    return await verify_user_email(token, db)

# 1.3. Đăng nhập
@router.post("/signin", response_model=AuthResponse)
async def signin(user_data: SigninRequest, db: Session = Depends(get_db)):
    """User login endpoint"""
    return await signin_user(user_data, db)
# 1.4. Đăng xuất
@router.get("/signout", response_model=MessageResponse)
async def signout(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """User logout endpoint"""
    return await signout_user(credentials, db)

# 1.5. Quên mật khẩu
@router.post("/forget-password", response_model=MessageResponse)
async def forget_password(request: ForgetPasswordRequest, db: Session = Depends(get_db)):
    """Forget password endpoint"""
    return await request_password_reset(request, db)

# 1.5.1. Kiểm tra token reset password
@router.get("/validate-reset-token/{token}", response_model=MessageResponse)
async def validate_reset_token(token: str, db: Session = Depends(get_db)):
    """Validate reset token endpoint"""
    return await validate_password_reset_token(token, db)

# 1.6. Đặt lại mật khẩu
@router.post("/reset-password/{token}", response_model=MessageResponse)
async def reset_password(token: str, request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password endpoint"""
    return await reset_user_password(token, request, db)

# 1.7. Đăng nhập bằng tài khoản thứ ba (Google)
@router.post("/oauth-signin", response_model=AuthResponse)
async def oauth_signin(request: OAuthSigninRequest, db: Session = Depends(get_db)):
    """OAuth signin endpoint (Google)"""
    return await oauth_signin_user(request, db)

# 1.8. Đổi mật khẩu
@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password endpoint"""
    return await change_user_password(request, current_user, db)

# 1.9. Đăng nhập cho ADMIN
@router.post("/admin/signin", response_model=AuthResponse)
async def admin_signin(request: AdminSigninRequest, db: Session = Depends(get_db)):
    """Admin login endpoint"""
    return await admin_signin_user(request, db)

# 1.10. Gửi lại email xác thực
@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(request: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend verification email endpoint"""
    return await resend_verification_email(request, db)
