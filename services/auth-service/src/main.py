import sys
import os

# Add libs path to use common utilities  
sys.path.insert(0, '/app/libs/common-utils-py/src')

from fastapi import FastAPI, HTTPException, Depends, status, Response, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import bcrypt
import jwt
import secrets
import time
from datetime import datetime, timedelta, timezone
import uuid
from datetime import datetime, timedelta
import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlight_common import get_jwt_config, get_service_port

# Load JWT configuration from common utilities
jwt_config = get_jwt_config()

from src.database import get_db, create_tables
from src.models import User, Admin, TokenBlacklist

# Import database URL
from pathlight_common import get_database_url
DATABASE_URL = get_database_url()

# Email verification configuration
EMAIL_VERIFICATION_EXPIRE_MINUTES = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "10"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service", version="1.0.0")

# Load configuration from environment
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "pathlight-refresh-secret-key-2025")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
ALLOWED_METHODS = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
ALLOWED_HEADERS = os.getenv("ALLOWED_HEADERS", "*").split(",")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@pathlight.com")

# Frontend URL
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

# Security
security = HTTPBearer()

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Data Models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class SigninRequest(BaseModel):
    email: EmailStr
    password: str

class ForgetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    new_password: str

class ChangePasswordRequest(BaseModel):
    password: str
    new_password: str

class OAuthSigninRequest(BaseModel):
    email: EmailStr
    google_id: str
    given_name: str
    family_name: str
    avatar_id: str

class AdminSigninRequest(BaseModel):
    username: str
    password: str

class MessageResponse(BaseModel):
    status: int
    message: Optional[str] = None

class AuthResponse(BaseModel):
    status: int
    access_token: Optional[str] = None
    message: Optional[str] = None

class ResendVerificationRequest(BaseModel):
    email: EmailStr

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP with improved reliability"""
    try:
        logger.info(f"🔍 DEBUG: Attempting to send email to {to_email}")
        logger.info(f"🔍 DEBUG: SMTP_USERNAME={SMTP_USERNAME}")
        logger.info(f"🔍 DEBUG: SMTP_PASSWORD={'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'EMPTY'}")
        logger.info(f"🔍 DEBUG: FROM_EMAIL={FROM_EMAIL}")
        logger.info(f"🔍 DEBUG: SMTP_SERVER={SMTP_SERVER}:{SMTP_PORT}")
        
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("Email credentials not configured. Skipping email send.")
            return
            
        logger.info(f"📧 Creating email message...")
        msg = MIMEMultipart('alternative')
        msg['From'] = f"PathLight <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Message-ID'] = f"<{secrets.token_urlsafe(16)}@pathlight.com>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['X-Mailer'] = 'PathLight App'
        
        # Add both HTML and plain text versions
        plain_body = body.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n')
        plain_body = plain_body.replace('<strong>', '').replace('</strong>', '')
        plain_body = plain_body.replace('<a href="', '').replace('">', ' ').replace('</a>', '')
        
        text_part = MIMEText(plain_body, 'plain', 'utf-8')
        html_part = MIMEText(body, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Try sending with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"📡 Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT} (attempt {attempt + 1}/{max_retries})...")
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
                
                logger.info(f"🔒 Starting TLS...")
                server.starttls()
                
                logger.info(f"🔑 Logging in...")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                
                logger.info(f"📤 Sending email...")
                refused = server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
                
                if refused:
                    logger.warning(f"⚠️ Some recipients were refused: {refused}")
                else:
                    logger.info(f"✅ Email sent successfully to {to_email}")
                
                server.quit()
                return  # Success, exit retry loop
                
            except smtplib.SMTPException as smtp_error:
                logger.error(f"❌ SMTP error on attempt {attempt + 1}: {str(smtp_error)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as conn_error:
                logger.error(f"❌ Connection error on attempt {attempt + 1}: {str(conn_error)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
                
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        import traceback
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        # Print Vietnamese error message for debugging
        print(f"Lỗi không gửi email đến {to_email}: {str(e)}")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Startup event
@app.on_event("startup")
async def startup_event():
    # Create tables
    create_tables()
    
    # Create default admin user
    from src.database import SessionLocal
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.username == ADMIN_USERNAME).first()
        if not admin:
            admin = Admin(
                username=ADMIN_USERNAME,
                password=hash_password(ADMIN_PASSWORD)
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user created")
    finally:
        db.close()

# Health endpoints
@app.get("/")
async def root():
    return {"message": "Auth Service is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-service"}

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration"""
    return {
        "FRONTEND_URL": FRONTEND_URL,
        "DATABASE_URL": DATABASE_URL[:50] + "..." if DATABASE_URL else None,  # Hide sensitive data
        "JWT_SECRET_KEY": JWT_SECRET_KEY[:10] + "..." if JWT_SECRET_KEY else None,
        "SMTP_USERNAME": SMTP_USERNAME,
        "EMAIL_VERIFICATION_EXPIRE_MINUTES": EMAIL_VERIFICATION_EXPIRE_MINUTES,
    }

# 1.1. Đăng ký
@app.post("/api/v1/signup", response_model=MessageResponse)
async def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    """User registration endpoint"""
    try:
        logger.info(f"Signup attempt for email: {user_data.email}")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        
        if existing_user:
            if existing_user.is_email_verified:
                # User exists and is verified - REJECT signup
                logger.warning(f"Attempted signup with already verified email: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email này đã được sử dụng và đã được xác thực. Vui lòng đăng nhập hoặc sử dụng email khác."
                )
            else:
                # User exists but not verified - allow re-registration with new verification token
                logger.info(f"Re-registering unverified user: {user_data.email}")
                verification_token = generate_token()
                expire_minutes = EMAIL_VERIFICATION_EXPIRE_MINUTES
                expiration_time = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
                
                existing_user.email_verification_token = verification_token
                existing_user.email_verification_expires_at = expiration_time
                existing_user.password = hash_password(user_data.password)  # Update password
                db.commit()
                
                # Send verification email with proper URL
                frontend_base = FRONTEND_URL.rstrip('/')
                if frontend_base == "*" or not frontend_base.startswith(('http://', 'https://')):
                    frontend_base = "http://localhost:3000"  # Default fallback
                
                verification_link = f"{frontend_base}/auth/verify-email?token={verification_token}"
                logger.info(f"Re-registration verification link: {verification_link}")
                
                email_body = f"""
                <html>
                <body>
                    <h2>Xác thực tài khoản PathLight</h2>
                    <p>Chào bạn,</p>
                    <p>Bạn đã đăng ký lại tài khoản với email này!</p>
                    <p>Vui lòng click vào nút dưới đây để xác thực tài khoản của bạn:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}" style="background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Xác thực tài khoản</a>
                    </p>
                    <p>Hoặc copy và paste link sau vào trình duyệt:</p>
                    <p style="word-break: break-all; color: #666;">{verification_link}</p>
                    <p style="color: #999; font-size: 12px;">Link này sẽ hết hạn sau {expire_minutes} phút.</p>
                </body>
                </html>
                """
                
                send_email(user_data.email, "Xác thực tài khoản (Đăng ký lại)", email_body)
                return MessageResponse(status=200, message="Email đã được đăng ký trước đó nhưng chưa xác thực. Mã xác thực mới đã được gửi vào email của bạn.")
        
        # Create new user (email doesn't exist)
        logger.info(f"Creating new user: {user_data.email}")
        verification_token = generate_token()
        expire_minutes = EMAIL_VERIFICATION_EXPIRE_MINUTES
        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        hashed_password = hash_password(user_data.password)
        
        user = User(
            email=user_data.email,
            password=hashed_password,
            email_verification_token=verification_token,
            email_verification_expires_at=expiration_time,
            is_email_verified=False
        )
        
        db.add(user)
        db.commit()
        
        # Send verification email with proper URL formatting
        frontend_base = FRONTEND_URL.rstrip('/')
        if frontend_base == "*" or not frontend_base.startswith(('http://', 'https://')):
            frontend_base = "http://localhost:3000"  # Default fallback
        
        verification_link = f"{frontend_base}/auth/verify-email?token={verification_token}"
        logger.info(f"Generated verification link: {verification_link}")
        
        email_body = f"""
        <html>
        <body>
            <h2>Xác thực tài khoản PathLight</h2>
            <p>Chào bạn,</p>
            <p>Cảm ơn bạn đã đăng ký tài khoản tại PathLight!</p>
            <p>Vui lòng click vào nút dưới đây để xác thực tài khoản của bạn:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Xác thực tài khoản</a>
            </p>
            <p>Hoặc copy và paste link sau vào trình duyệt:</p>
            <p style="word-break: break-all; color: #666;">{verification_link}</p>
            <p style="color: #999; font-size: 12px;">Link này sẽ hết hạn sau {expire_minutes} phút.</p>
        </body>
        </html>
        """
        
        send_email(user_data.email, "Xác thực tài khoản PathLight", email_body)
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

# 1.2. Xác thực Email
@app.get("/api/v1/verify-email", response_model=MessageResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email endpoint"""
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        return MessageResponse(status=401, message="Token không hợp lệ hoặc đã hết hạn")
    
    # Check if token has expired
    expiration_time = user.email_verification_expires_at
    if expiration_time is not None and expiration_time < datetime.now(timezone.utc):
        return MessageResponse(status=401, message="Token đã hết hạn. Vui lòng yêu cầu gửi lại email xác nhận")
    
    # Update user as verified
    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expires_at = None
    db.commit()
    
    return MessageResponse(status=200, message="Email đã được xác thực thành công")

# 1.3. Đăng nhập
@app.post("/api/v1/signin", response_model=AuthResponse)
async def signin(user_data: SigninRequest, db: Session = Depends(get_db)):
    """User login endpoint"""
    try:
        logger.info(f"Login attempt for email: {user_data.email}")
        
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user:
            logger.warning(f"Login failed: User not found for email {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng"
            )
        
        if not user.password or not verify_password(user_data.password, user.password):
            logger.warning(f"Login failed: Invalid password for email {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng"
            )
        
        if not user.is_email_verified:
            logger.warning(f"Login failed: Email not verified for {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email chưa được xác thực"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        logger.info(f"Login successful for email: {user_data.email}")
        
        return AuthResponse(status=200, access_token=access_token)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {user_data.email}: {str(e)}")
        import traceback
        logger.error(f"Signin traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi server. Vui lòng thử lại sau"
        )

# 1.4. Đăng xuất
@app.get("/api/v1/signout", response_model=MessageResponse)
async def signout(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """User logout endpoint"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        jti = payload.get("jti")
        
        if jti:
            # Add token to blacklist
            blacklist_token = TokenBlacklist(token_jti=jti)
            db.add(blacklist_token)
            db.commit()
    except:
        pass
    
    return MessageResponse(status=200)

# 1.5. Quên mật khẩu
@app.post("/api/v1/forget-password", response_model=MessageResponse)
async def forget_password(request: ForgetPasswordRequest, db: Session = Depends(get_db)):
    """Forget password endpoint"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # User doesn't exist
        logger.warning(f"Password reset requested for non-existent email: {request.email}")
        return MessageResponse(status=404, message="Email này không tồn tại trong hệ thống")
    
    if not user.password:
        # User exists but is OAuth-only (no password to reset)
        logger.warning(f"Password reset requested for OAuth-only user: {request.email}")
        return MessageResponse(status=400, message="Tài khoản này đăng nhập bằng Google, không thể đặt lại mật khẩu")
    
    if not getattr(user, 'is_active', True):
        # User exists but is inactive
        logger.warning(f"Password reset requested for inactive user: {request.email}")
        return MessageResponse(status=403, message="Tài khoản này đã bị vô hiệu hóa")
    
    # User exists, has password, and is active - send reset email
    reset_token = generate_token()
    user.password_reset_token = reset_token
    db.commit()
    
    # Send reset email
    reset_link = f"{FRONTEND_URL}/api/v1/reset-password/{reset_token}"
    email_body = f"""
    <html>
    <body>
        <h2>Đặt lại mật khẩu</h2>
        <p>Chào bạn,</p>
        <p>Vui lòng click vào link dưới đây để đặt lại mật khẩu:</p>
        <a href="{reset_link}">Đặt lại mật khẩu</a>
        <p>Link này sẽ hết hạn sau 10 phút.</p>
    </body>
    </html>
    """
    
    send_email(request.email, "Đặt lại mật khẩu", email_body)
    logger.info(f"Password reset email sent to {request.email}")
    
    return MessageResponse(status=200, message="Email đặt lại mật khẩu đã được gửi. Vui lòng kiểm tra hộp thư của bạn")

# 1.5.1. Kiểm tra token reset password
@app.get("/api/v1/validate-reset-token/{token}", response_model=MessageResponse)
async def validate_reset_token(token: str, db: Session = Depends(get_db)):
    """Validate reset token endpoint"""
    user = db.query(User).filter(User.password_reset_token == token).first()
    
    if not user:
        # Token not found or invalid
        logger.warning(f"Token validation failed - invalid token: {token[:8]}...")
        return MessageResponse(status=401, message="Token không hợp lệ hoặc đã hết hạn")
    
    if not user.password:
        # User exists but is OAuth-only (no password to reset)
        logger.warning(f"Token validation failed - OAuth-only user: {user.email}")
        return MessageResponse(status=400, message="Tài khoản này đăng nhập bằng Google, không thể đặt lại mật khẩu")
    
    if not getattr(user, 'is_active', True):
        # User exists but is inactive
        logger.warning(f"Token validation failed - inactive user: {user.email}")
        return MessageResponse(status=403, message="Tài khoản này đã bị vô hiệu hóa")
    
    logger.info(f"Token validation successful for user: {user.email}")
    return MessageResponse(status=200, message="Token hợp lệ")

# 1.6. Đặt lại mật khẩu
@app.post("/api/v1/reset-password/{token}", response_model=MessageResponse)
async def reset_password(token: str, request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password endpoint"""
    user = db.query(User).filter(User.password_reset_token == token).first()
    
    if not user:
        # Token not found or invalid
        logger.warning(f"Reset password attempted with invalid token: {token[:8]}...")
        return MessageResponse(status=401, message="Token đã hết hạn hoặc không hợp lệ")
    
    if not user.password:
        # User exists but is OAuth-only (no password to reset)
        logger.warning(f"Reset password attempted for OAuth-only user: {user.email}")
        return MessageResponse(status=400, message="Tài khoản này đăng nhập bằng Google, không thể đặt lại mật khẩu")
    
    if not getattr(user, 'is_active', True):
        # User exists but is inactive
        logger.warning(f"Reset password attempted for inactive user: {user.email}")
        return MessageResponse(status=403, message="Tài khoản này đã bị vô hiệu hóa")
    
    # Check if new password is same as current password in database
    if verify_password(request.new_password, user.password):
        logger.warning(f"User {user.email} attempted to use same password during reset")
        return MessageResponse(status=409, message="Mật khẩu mới không được trùng với mật khẩu cũ")
    
    # Update password and clear reset token
    user.password = hash_password(request.new_password)
    user.password_reset_token = None
    db.commit()
    
    logger.info(f"Password reset successful for user {user.email}")
    return MessageResponse(status=200, message="Đặt lại mật khẩu thành công")

# 1.7. Đăng nhập bằng tài khoản thứ ba (Google)
@app.post("/api/v1/oauth-signin", response_model=AuthResponse)
async def oauth_signin(request: OAuthSigninRequest, db: Session = Depends(get_db)):
    """OAuth signin endpoint"""
    try:
        # Check if user exists by email or google_id
        user = db.query(User).filter(
            (User.email == request.email) | (User.google_id == request.google_id)
        ).first()
        
        if user:
            # Update user info
            user.google_id = request.google_id
            user.given_name = request.given_name
            user.family_name = request.family_name
            user.avatar_url = request.avatar_id
            user.is_email_verified = True
        else:
            # Create new user
            user = User(
                email=request.email,
                google_id=request.google_id,
                given_name=request.given_name,
                family_name=request.family_name,
                avatar_url=request.avatar_id,
                is_email_verified=True
            )
            db.add(user)
        
        db.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        return AuthResponse(status=200, access_token=access_token)
    except Exception as e:
        logger.error(f"OAuth signin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Có lỗi xảy ra, xin vui lòng thử lại"
        )

# 1.8. Đổi mật khẩu
@app.post("/api/v1/user/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password endpoint"""
    # Check if user is OAuth user
    if current_user.google_id and not current_user.password:
        return MessageResponse(status=401, message="Tài khoản này là của bên thứ ba, không thể đổi mật khẩu")
    
    # Verify current password
    if not current_user.password or not verify_password(request.password, current_user.password):
        return MessageResponse(status=401, message="Mật khẩu hiện tại không đúng")
    
    # Update password
    current_user.password = hash_password(request.new_password)
    db.commit()
    
    return MessageResponse(status=200)

# 1.9. Đăng nhập cho ADMIN
@app.post("/api/v1/admin/signin", response_model=AuthResponse)
async def admin_signin(request: AdminSigninRequest, db: Session = Depends(get_db)):
    """Admin login endpoint"""
    admin = db.query(Admin).filter(Admin.username == request.username).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    
    if not verify_password(request.password, admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    
    # Create access token with admin role
    access_token = create_access_token(data={"sub": admin.id, "role": "admin"})
    
    return AuthResponse(status=200, access_token=access_token)

# 1.2. Gửi lại email xác thực
@app.post("/api/v1/resend-verification", response_model=MessageResponse)
async def resend_verification(request: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend verification email endpoint"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        return MessageResponse(status=400, message="Email không tồn tại trong hệ thống")
    
    if user.is_email_verified is True:
        return MessageResponse(status=400, message="Email này đã được xác thực")
    
    # Generate new verification token
    verification_token = generate_token()
    expire_minutes = EMAIL_VERIFICATION_EXPIRE_MINUTES
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    
    user.email_verification_token = verification_token
    user.email_verification_expires_at = expiration_time
    db.commit()
    
    # Send verification email
    verification_link = f"{FRONTEND_URL}/auth/verify-email?token={verification_token}"
    email_body = f"""
    <html>
    <body>
        <h2>Xác thực tài khoản PathLight</h2>
        <p>Chào bạn,</p>
        <p>Bạn đã yêu cầu gửi lại email xác thực!</p>
        <p>Vui lòng click vào nút dưới đây để xác thực tài khoản của bạn:</p>
        <p style="text-align: start; margin: 30px 0;">
            <a href="{verification_link}" style="background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Xác thực tài khoản</a>
        </p>
        <p>Hoặc copy và paste link sau vào trình duyệt:</p>
        <p style="word-break: break-all; color: #666;">{verification_link}</p>
        <p style="color: #999; font-size: 12px;">Link này sẽ hết hạn sau 24 giờ.</p>
    </body>
    </html>
    """
    
    send_email(request.email, "Xác thực tài khoản (Gửi lại)", email_body)
    
    return MessageResponse(status=200, message="Email xác thực đã được gửi lại. Vui lòng kiểm tra hộp thư của bạn")

# Test email endpoint
@app.post("/api/v1/test-email")
async def test_email(email: str):
    """Test endpoint to send email directly"""
    try:
        test_body = """
        <h2>🧪 Test Email từ PathLight</h2>
        <p>Đây là email test để kiểm tra chức năng gửi email.</p>
        <p>Nếu bạn nhận được email này, hệ thống email đang hoạt động bình thường.</p>
        <p>Thời gian gửi: {}</p>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        send_email(email, "🧪 Test Email - PathLight", test_body)
        return {"message": f"Test email sent to {email}", "status": "success"}
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        return {"message": f"Failed to send test email: {str(e)}", "status": "error"}

# Test password verification endpoint (for debugging)
@app.post("/api/v1/test-password-verification")
async def test_password_verification(
    email: str, 
    test_password: str, 
    db: Session = Depends(get_db)
):
    """Test endpoint to verify password logic - REMOVE IN PRODUCTION"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "User not found", "status": "error"}
    
    if not user.password:
        return {"message": "User has no password (OAuth-only)", "status": "no_password"}
    
    # Test password verification
    is_same = verify_password(test_password, user.password)
    
    return {
        "message": f"Password comparison result: {'SAME' if is_same else 'DIFFERENT'}",
        "user_email": email,
        "has_password": bool(user.password),
        "password_hash_preview": user.password[:20] + "..." if user.password else None,
        "test_password": test_password,
        "verification_result": is_same,
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment
    port = int(os.getenv("AUTH_SERVICE_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
