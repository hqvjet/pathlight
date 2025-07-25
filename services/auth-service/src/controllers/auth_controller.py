import logging
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt as jose_jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config import config
from ..database import get_db
from ..models import User, TokenBlacklist
from ..schemas.auth_schemas import *
from ..services.auth_service import *
from ..services.email_service import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)
security = HTTPBearer()

from ..config import config

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jose_jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
        jti = payload.get("jti")
        if jti and is_token_blacklisted(db, jti):
            logger.error(f"Token is blacklisted: {jti}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been blacklisted")
        if payload.get("type") != "access":
            logger.error(f"Invalid token type: {payload.get('type')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token type: {payload.get('type')}")
        user_id = payload.get("sub")
        if user_id is None:
            logger.error("No user ID in token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no user id")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found in database: {user_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        is_email_verified = getattr(user, 'is_email_verified', False)
        is_active = getattr(user, 'is_active', True)
        if not is_email_verified:
            logger.error(f"Email not verified for user: {user.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")
        if not is_active:
            logger.error(f"User account inactive: {user.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive")
        logger.info(f"Authentication successful for user: {user.email}")
        return user
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token expired or invalid: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")

async def signup_user(user_data: SignupRequest, db: Session) -> MessageResponse:
    """Handle user registration"""
    try:
        existing_user = get_user_by_email(db, user_data.email)
        verification_expire_minutes = getattr(config, "EMAIL_VERIFICATION_EXPIRE_MINUTES", 10)
        if existing_user:
            if getattr(existing_user, 'google_id', None):
                logger.error(f"Attempted signup with Google account already exists: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tài khoản này đã đăng nhập bằng Google. Vui lòng đăng nhập bằng Google hoặc quên mật khẩu để đăng nhập."
                )
            if getattr(existing_user, 'is_email_verified'):
                logger.error(f"Attempted signup with already verified email: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email này đã được sử dụng và đã được xác thực. Vui lòng đăng nhập hoặc sử dụng email khác."
                )
            else:
                verification_token = generate_token()
                expiration_time = datetime.now(timezone.utc) + timedelta(minutes=verification_expire_minutes)
                setattr(existing_user, 'email_verification_token', verification_token)
                setattr(existing_user, 'email_verification_expires_at', expiration_time)
                setattr(existing_user, 'password', hash_password(user_data.password))
                db.commit()
                send_verification_email(user_data.email, verification_token, verification_expire_minutes)
                logger.info(f"Signup success (re-register unverified) for email: {user_data.email}")
                return MessageResponse(status=200, message="Email đã được đăng ký trước đó nhưng chưa xác thực. Mã xác thực mới đã được gửi vào email của bạn.")
        google_id = user_data.google_id if user_data.google_id else None
        user = create_user(db, user_data.email, user_data.password, google_id)
        send_verification_email(user_data.email, getattr(user, 'email_verification_token'), verification_expire_minutes)
        logger.info(f"Signup successful for email: {user_data.email}")
        return MessageResponse(status=200, message="Mã xác thực đã được gửi vào email của bạn, xin vui lòng xác thực email của bạn")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error for {user_data.email}: {str(e)}")
        import traceback
        logger.error(f"Signup traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi server. Vui lòng thử lại sau"
        )

async def verify_user_email(token: str, db: Session) -> AuthResponse:
    """Verify user email with token"""
    user = get_user_by_verification_token(db, token)
    verification_expire_minutes = getattr(config, "EMAIL_VERIFICATION_EXPIRE_MINUTES", 10)
    if not user:
        return AuthResponse(
            status=401, 
            message="Token không hợp lệ hoặc đã hết hạn",
            access_token=None
        )
    expiration_time = getattr(user, 'email_verification_expires_at')
    if expiration_time is not None and expiration_time < datetime.now(timezone.utc):
        return AuthResponse(
            status=401, 
            message="Token đã hết hạn. Vui lòng yêu cầu gửi lại email xác nhận",
            access_token=None
        )
    verify_email_token(db, user)
    access_token = create_access_token(data={"sub": user.id})
    logger.info(f"Email verified for user: {user.email}")
    return AuthResponse(
        status=200,
        message="Email đã được xác thực thành công",
        access_token=access_token
    )

async def signin_user(user_data: SigninRequest, db: Session) -> AuthResponse:
    """Handle user login"""
    try:
        logger.info(f"Login attempt for email: {user_data.email}")
        
        user = get_user_by_email(db, user_data.email)
        if not user:
            logger.warning(f"Login failed: User not found for email {user_data.email}")
            return AuthResponse(
                status=401,
                message="Email hoặc mật khẩu không đúng",
                access_token=None
            )
        
        user_password = getattr(user, 'password')
        if not user_password or not verify_password(user_data.password, user_password):
            logger.warning(f"Login failed: Invalid password for email {user_data.email}")
            return AuthResponse(
                status=401,
                message="Email hoặc mật khẩu không đúng",
                access_token=None
            )
        
        if not getattr(user, 'is_email_verified'):
            logger.warning(f"Login failed: Email not verified for {user_data.email}")
            return AuthResponse(
                status=401,
                message="Email chưa được xác thực",
                access_token=None
            )
        
        access_token = create_access_token(data={"sub": user.id})
        logger.info(f"Login successful for email: {user_data.email}")
        
        return AuthResponse(status=200, access_token=access_token)
        
    except Exception as e:
        logger.error(f"Login error for {user_data.email}: {str(e)}")
        import traceback
        logger.error(f"Signin traceback: {traceback.format_exc()}")
        return AuthResponse(
            status=500,
            message="Lỗi server. Vui lòng thử lại sau",
            access_token=None
        )

async def signout_user(credentials: HTTPAuthorizationCredentials, db: Session) -> MessageResponse:
    """Handle user logout"""
    token = credentials.credentials
    try:
        payload = jose_jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
        jti = payload.get("jti")
        if jti:
            blacklist_token(db, jti)
            logger.info(f"Signout: token {jti} blacklisted")
    except Exception as e:
        logger.error(f"Signout: failed to blacklist token: {str(e)}")
    return MessageResponse(status=200)

async def request_password_reset(request: ForgetPasswordRequest, db: Session) -> MessageResponse:
    """Handle password reset request"""
    try:
        user = get_user_by_email(db, request.email)
        if not user:
            logger.error(f"Password reset requested for non-existent email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email này không tồn tại trong hệ thống"
            )
        user_password = getattr(user, 'password')
        if not user_password:
            logger.error(f"Password reset requested for OAuth-only user: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản này đăng nhập bằng Google, không thể đặt lại mật khẩu"
            )
        reset_token = generate_token()
        setattr(user, 'password_reset_token', reset_token)
        db.commit()
        send_password_reset_email(request.email, reset_token)
        logger.info(f"Password reset email sent to {request.email}")
        return MessageResponse(status=200, message="Email đặt lại mật khẩu đã được gửi. Vui lòng kiểm tra hộp thư của bạn")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forget password error for {request.email}: {str(e)}")
        import traceback
        logger.error(f"Forget password traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi server. Vui lòng thử lại sau"
        )

async def validate_password_reset_token(token: str, db: Session) -> MessageResponse:
    """Validate password reset token"""
    user = get_user_by_reset_token(db, token)
    
    if not user:
        logger.warning(f"Token validation failed - invalid token: {token[:8]}...")
        return MessageResponse(status=401, message="Token không hợp lệ hoặc đã hết hạn")
    
    user_password = getattr(user, 'password')
    if not user_password:
        logger.warning(f"Token validation failed - OAuth-only user: {user.email}")
        return MessageResponse(status=400, message="Tài khoản này đăng nhập bằng Google, không thể đặt lại mật khẩu")
    
    if not getattr(user, 'is_active', True):
        logger.warning(f"Token validation failed - inactive user: {user.email}")
        return MessageResponse(status=403, message="Tài khoản này đã bị vô hiệu hóa")
    
    logger.info(f"Token validation successful for user: {user.email}")
    return MessageResponse(status=200, message="Token hợp lệ")

async def reset_user_password(token: str, request: ResetPasswordRequest, db: Session) -> MessageResponse:
    """Reset user password"""
    user = get_user_by_reset_token(db, token)
    
    if not user:
        logger.warning(f"Reset password attempted with invalid token: {token[:8]}...")
        return MessageResponse(status=401, message="Token đã hết hạn hoặc không hợp lệ")
    
    user_password = getattr(user, 'password')
    if not user_password:
        logger.warning(f"Reset password attempted for OAuth-only user: {user.email}")
        return MessageResponse(status=400, message="Tài khoản này đăng nhập bằng Google, không thể đặt lại mật khẩu")
    
    if not getattr(user, 'is_active', True):
        logger.warning(f"Reset password attempted for inactive user: {user.email}")
        return MessageResponse(status=403, message="Tài khoản này đã bị vô hiệu hóa")
    
    if verify_password(request.new_password, user_password):
        logger.warning(f"User {user.email} attempted to use same password during reset")
        return MessageResponse(status=409, message="Mật khẩu mới không được trùng với mật khẩu cũ")
    
    setattr(user, 'password', hash_password(request.new_password))
    setattr(user, 'password_reset_token', None)
    db.commit()
    
    logger.info(f"Password reset successful for user {user.email}")
    return MessageResponse(status=200, message="Đặt lại mật khẩu thành công")

async def oauth_signin_user(request: OAuthSigninRequest, db: Session) -> AuthResponse:
    """Handle OAuth signin"""
    try:
        logger.info(f"OAuth signin attempt for email: {request.email}")
        
        user = db.query(User).filter(
            (User.email == request.email) | (User.google_id == request.google_id)
        ).first()
        
        if user:
            logger.info(f"Found existing user for OAuth signin: {user.email}")
            
            if not getattr(user, 'google_id', None):
                setattr(user, 'google_id', request.google_id)
            
            if not getattr(user, 'given_name', None):
                setattr(user, 'given_name', request.given_name)
            
            if not getattr(user, 'family_name', None):
                setattr(user, 'family_name', request.family_name)
            
            current_avatar = getattr(user, 'avatar_url', None)
            if not current_avatar or (current_avatar and 'googleusercontent.com' in current_avatar):
                setattr(user, 'avatar_url', request.avatar_id)
            
            setattr(user, 'is_email_verified', True)
            setattr(user, 'is_active', True)
            
            if not getattr(user, 'password', None):
                setattr(user, 'password', hash_password(request.google_id))
        else:
            logger.info(f"Creating new user for OAuth signin: {request.email}")
            user = User(
                email=request.email,
                google_id=request.google_id,
                given_name=request.given_name,
                family_name=request.family_name,
                avatar_url=request.avatar_id,
                is_email_verified=True,
                is_active=True,
                password=hash_password(request.google_id)
            )
            db.add(user)
        
        db.commit()
        access_token = create_access_token(data={"sub": user.id})
        logger.info(f"OAuth signin successful for email: {request.email}")
        
        return AuthResponse(status=200, access_token=access_token)
        
    except Exception as e:
        logger.error(f"OAuth signin error for {request.email}: {str(e)}")
        import traceback
        logger.error(f"OAuth signin traceback: {traceback.format_exc()}")
        
        return AuthResponse(
            status=401,
            message="Đăng nhập Google thất bại. Vui lòng thử lại.",
            access_token=None
        )

async def change_user_password(request: ChangePasswordRequest, current_user: User, db: Session) -> MessageResponse:
    """Change user password"""
    user_google_id = getattr(current_user, 'google_id')
    user_password = getattr(current_user, 'password')
    if user_google_id and not user_password:
        return MessageResponse(status=401, message="Tài khoản này là của bên thứ ba, không thể đổi mật khẩu")
    
    if not user_password or not verify_password(request.password, user_password):
        return MessageResponse(status=401, message="Mật khẩu hiện tại không đúng")
    
    setattr(current_user, 'password', hash_password(request.new_password))
    db.commit()
    
    return MessageResponse(status=200)

async def admin_signin_user(request: AdminSigninRequest, db: Session) -> AuthResponse:
    """Handle admin login"""
    admin = get_admin_by_username(db, request.username)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    
    admin_password = getattr(admin, 'password')
    if not verify_password(request.password, admin_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    
    access_token = create_access_token(data={"sub": admin.id, "role": "admin"})
    return AuthResponse(status=200, access_token=access_token)

async def resend_verification_email(request: ResendVerificationRequest, db: Session) -> MessageResponse:
    """Resend verification email"""
    user = get_user_by_email(db, request.email)
    verification_expire_minutes = getattr(config, "EMAIL_VERIFICATION_EXPIRE_MINUTES", 10)
    if not user:
        return MessageResponse(status=400, message="Email không tồn tại trong hệ thống")
    if user.is_email_verified is True:
        return MessageResponse(status=400, message="Email này đã được xác thực")
    verification_token = generate_token()
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=verification_expire_minutes)
    setattr(user, 'email_verification_token', verification_token)
    setattr(user, 'email_verification_expires_at', expiration_time)
    db.commit()
    send_verification_email(request.email, verification_token, verification_expire_minutes)
    logger.info(f"Resent verification email to {request.email}")
    return MessageResponse(status=200, message="Email xác thực đã được gửi lại. Vui lòng kiểm tra hộp thư của bạn")