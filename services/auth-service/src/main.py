import sys
import os

# Add libs path to use common utilities
# For Docker: /app/libs/common-utils-py/src
# For local development: relative path
if os.path.exists('/app/libs/common-utils-py/src'):
    sys.path.insert(0, '/app/libs/common-utils-py/src')
    sys.path.insert(0, '/app/libs/common-types-py')
else:
    # Local development path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    libs_path = os.path.join(current_dir, '..', '..', '..', 'libs', 'common-utils-py', 'src')
    types_path = os.path.join(current_dir, '..', '..', '..', 'libs', 'common-types-py')
    sys.path.insert(0, os.path.abspath(libs_path))
    sys.path.insert(0, os.path.abspath(types_path))

from fastapi import FastAPI, HTTPException, Depends, status, Response, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import bcrypt
import jwt
from jose import JWTError, jwt as jose_jwt
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
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit

# Load JWT configuration from common utilities
jwt_config = get_jwt_config()

from src.database import get_db, create_tables, SessionLocal
from src.models import User, Admin, TokenBlacklist
from src.email_reminders import send_email

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

# Background Scheduler for Study Reminders
scheduler = BackgroundScheduler()

def run_study_reminders():
    try:
        logger.info("[REMINDER DEBUG] Scheduler đã gọi run_study_reminders()")
        db = SessionLocal()
        from src.email_reminders import send_reminders_to_users
        result = send_reminders_to_users(db)
        logger.info(f"[REMINDER DEBUG] Kết quả gửi nhắc nhở: {result}")
        db.close()
    except Exception as e:
        logger.error(f"[REMINDER DEBUG] Lỗi khi gửi nhắc nhở: {str(e)}")

# Schedule study reminders every 1 minute (dễ test)
scheduler.add_job(
    func=run_study_reminders,
    trigger=CronTrigger(minute="*"),  # Mỗi phút chạy 1 lần
    id='study_reminders',
    name='Send study reminder emails',
    replace_existing=True
)

# Start scheduler
scheduler.start()
logger.info("Background scheduler started for study reminders")

# Ensure scheduler shuts down when app stops
atexit.register(lambda: scheduler.shutdown())

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
    family_name: Optional[str] = None
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

class NotifyTimeRequest(BaseModel):
    remind_time: str
    
    @validator('remind_time')
    def validate_time_format(cls, v):
        # Validate HH:MM format
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format (e.g., "18:30")')
        return v

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "type": "access",
        "iat": int(now.timestamp())
    })
    return jose_jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "type": "refresh", 
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp())
    })
    return jose_jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

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
        logger.info(f"🔍 get_current_user: Processing token: {token[:20]}...")

        try:
            payload = jose_jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError as e:
            logger.error(f"🔍 get_current_user: JWT Error: {str(e)}")
            logger.error(f"🔍 get_current_user: Token that failed: {token}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token expired or invalid: {str(e)}")

        logger.info(f"🔍 get_current_user: Token decoded successfully. Payload: {payload}")

        jti = payload.get("jti")
        if jti:
            blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first()
            if blacklisted:
                logger.warning(f"🔍 get_current_user: Token is blacklisted: {jti}")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been blacklisted")

        if payload.get("type") != "access":
            logger.warning(f"🔍 get_current_user: Invalid token type: {payload.get('type')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token type: {payload.get('type')}")

        user_id = payload.get("sub")
        if user_id is None:
            logger.warning(f"🔍 get_current_user: No user ID in token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no user id")

        logger.info(f"🔍 get_current_user: Looking for user with ID: {user_id}")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"🔍 get_current_user: User not found in database: {user_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        is_email_verified = getattr(user, 'is_email_verified', False)
        is_active = getattr(user, 'is_active', True)

        logger.info(f"🔍 get_current_user: User {user.email} - email_verified: {is_email_verified}, active: {is_active}")

        if not is_email_verified:
            logger.warning(f"🔍 get_current_user: Email not verified for user: {user.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")

        if not is_active:
            logger.warning(f"🔍 get_current_user: User account inactive: {user.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive")

        logger.info(f"🔍 get_current_user: Authentication successful for user: {user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 get_current_user: Unexpected error: {str(e)}")
        import traceback
        logger.error(f"🔍 get_current_user: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")

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
            if getattr(existing_user, 'is_email_verified'):
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
                
                setattr(existing_user, 'email_verification_token', verification_token)
                setattr(existing_user, 'email_verification_expires_at', expiration_time)
                setattr(existing_user, 'password', hash_password(user_data.password))  # Update password
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
@app.get("/api/v1/verify-email", response_model=AuthResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email endpoint"""
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        return AuthResponse(
            status=401, 
            message="Token không hợp lệ hoặc đã hết hạn",
            access_token=None
        )
    
    # Check if token has expired
    expiration_time = getattr(user, 'email_verification_expires_at')
    if expiration_time is not None and expiration_time < datetime.now(timezone.utc):
        return AuthResponse(
            status=401, 
            message="Token đã hết hạn. Vui lòng yêu cầu gửi lại email xác nhận",
            access_token=None
        )
    
    # Update user as verified
    setattr(user, 'is_email_verified', True)
    setattr(user, 'email_verification_token', None)
    setattr(user, 'email_verification_expires_at', None)
    db.commit()
    
    # Generate JWT token for verified user
    access_token = create_access_token(data={"sub": user.id})
    
    logger.info(f"Email verified successfully for user: {user.email}")
    
    return AuthResponse(
        status=200,
        message="Email đã được xác thực thành công",
        access_token=access_token
    )

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
        
        user_password = getattr(user, 'password')
        if not user_password or not verify_password(user_data.password, user_password):
            logger.warning(f"Login failed: Invalid password for email {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng"
            )
        
        if not getattr(user, 'is_email_verified'):
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
        payload = jose_jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        jti = payload.get("jti")
        
        if jti:
            # Add token to blacklist
            blacklist_token = TokenBlacklist(token_jti=jti)
            db.add(blacklist_token)
            db.commit()
    except:
        pass
    
    return MessageResponse(status=200)

@app.post("/api/v1/forget-password", response_model=MessageResponse)
async def forget_password(request: ForgetPasswordRequest, db: Session = Depends(get_db)):
    """Forget password endpoint"""
    try:
        logger.info(f"Password reset requested for email: {request.email}")
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            # User doesn't exist
            logger.warning(f"Password reset requested for non-existent email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email này không tồn tại trong hệ thống"
            )
        
        # Check if user has a password (not OAuth-only)
        user_password = getattr(user, 'password')
        if not user_password:
            # User exists but is OAuth-only (no password to reset)
            logger.warning(f"Password reset requested for OAuth-only user: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản này đăng nhập bằng Google, không thể đặt lại mật khẩu"
            )
        
        # User exists and has password - send reset email (regardless of email verification status)
        reset_token = generate_token()
        setattr(user, 'password_reset_token', reset_token)
        db.commit()
        
        # Send reset email with proper URL formatting
        frontend_base = FRONTEND_URL.rstrip('/')
        if frontend_base == "*" or not frontend_base.startswith(('http://', 'https://')):
            frontend_base = "http://localhost:3000"  # Default fallback
        
        reset_link = f"{frontend_base}/auth/reset-password/{reset_token}"
        logger.info(f"Generated reset password link: {reset_link}")
        
        email_body = f"""
        <html>
        <body>
            <h2>Đặt lại mật khẩu PathLight</h2>
            <p>Chào bạn,</p>
            <p>Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản PathLight của mình.</p>
            <p>Vui lòng click vào nút dưới đây để đặt lại mật khẩu:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Đặt lại mật khẩu</a>
            </p>
            <p>Hoặc copy và paste link sau vào trình duyệt:</p>
            <p style="word-break: break-all; color: #666;">{reset_link}</p>
            <p style="color: #999; font-size: 12px;">Link này sẽ hết hạn sau 15 phút.</p>
            <p style="color: #999; font-size: 12px;">Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.</p>
        </body>
        </html>
        """
        
        send_email(request.email, "Đặt lại mật khẩu PathLight", email_body)
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

# 1.5.1. Kiểm tra token reset password
@app.get("/api/v1/validate-reset-token/{token}", response_model=MessageResponse)
async def validate_reset_token(token: str, db: Session = Depends(get_db)):
    """Validate reset token endpoint"""
    user = db.query(User).filter(User.password_reset_token == token).first()
    
    if not user:
        # Token not found or invalid
        logger.warning(f"Token validation failed - invalid token: {token[:8]}...")
        return MessageResponse(status=401, message="Token không hợp lệ hoặc đã hết hạn")
    
    user_password = getattr(user, 'password')
    if not user_password:
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
    
    user_password = getattr(user, 'password')
    if not user_password:
        # User exists but is OAuth-only (no password to reset)
        logger.warning(f"Reset password attempted for OAuth-only user: {user.email}")
        return MessageResponse(status=400, message="Tài khoản này đăng nhập bằng Google, không thể đặt lại mật khẩu")
    
    if not getattr(user, 'is_active', True):
        # User exists but is inactive
        logger.warning(f"Reset password attempted for inactive user: {user.email}")
        return MessageResponse(status=403, message="Tài khoản này đã bị vô hiệu hóa")
    
    # Check if new password is same as current password in database
    if verify_password(request.new_password, user_password):
        logger.warning(f"User {user.email} attempted to use same password during reset")
        return MessageResponse(status=409, message="Mật khẩu mới không được trùng với mật khẩu cũ")
    
    # Update password and clear reset token
    setattr(user, 'password', hash_password(request.new_password))
    setattr(user, 'password_reset_token', None)
    db.commit()
    
    logger.info(f"Password reset successful for user {user.email}")
    return MessageResponse(status=200, message="Đặt lại mật khẩu thành công")

# 1.7. Đăng nhập bằng tài khoản thứ ba (Google)
@app.post("/api/v1/oauth-signin", response_model=AuthResponse)
async def oauth_signin(request: OAuthSigninRequest, db: Session = Depends(get_db)):
    """OAuth signin endpoint (Google)"""
    try:
        user = db.query(User).filter(
            (User.email == request.email) | (User.google_id == request.google_id)
        ).first()
        
        if user:
            # Update user info
            setattr(user, 'google_id', request.google_id)
            setattr(user, 'given_name', request.given_name)
            setattr(user, 'family_name', request.family_name)
            setattr(user, 'avatar_url', request.avatar_id)
            setattr(user, 'is_email_verified', True)
            setattr(user, 'is_active', True)
        else:
            # Create new user
            user = User(
                email=request.email,
                google_id=request.google_id,
                given_name=request.given_name,
                family_name=request.family_name,
                avatar_url=request.avatar_id,
                is_email_verified=True,
                is_active=True
            )
            db.add(user)
        db.commit()
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
    user_google_id = getattr(current_user, 'google_id')
    user_password = getattr(current_user, 'password')
    if user_google_id and not user_password:
        return MessageResponse(status=401, message="Tài khoản này là của bên thứ ba, không thể đổi mật khẩu")
    
    # Verify current password
    if not user_password or not verify_password(request.password, user_password):
        return MessageResponse(status=401, message="Mật khẩu hiện tại không đúng")
    
    # Update password
    setattr(current_user, 'password', hash_password(request.new_password))
    db.commit()
    
    return MessageResponse(status=200)

# 1.8b. Đặt thời gian nhắc học tập
@app.put("/api/v1/user/notify-time", response_model=MessageResponse)
async def set_notify_time(
    request: NotifyTimeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set study reminder time for user"""
    try:
        logger.info(f"Setting notify time for user {current_user.email}: {request.remind_time}")
        # Always allow setting/updating remind_time
        setattr(current_user, 'remind_time', request.remind_time)
        db.commit()
        logger.info(f"Successfully set remind time for user {current_user.email} to {request.remind_time}")
        return MessageResponse(
            status=200, 
            message="Đã đặt lịch thành công"
        )
    except Exception as e:
        logger.error(f"Failed to set remind time for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        return MessageResponse(
            status=500, 
            message="Có lỗi xảy ra, xin vui lòng thử lại"
        )

# 1.8d. Get users with reminder settings (for admin checking)
@app.get("/api/v1/admin/users-with-reminders")
async def get_users_with_reminders(db: Session = Depends(get_db)):
    """Get list of users who have set reminder times"""
    try:
        users = db.query(User).filter(
            User.remind_time.isnot(None),
            User.is_email_verified == True,
            User.is_active == True
        ).all()
        
        result = []
        for user in users:
            created_at_value = getattr(user, 'created_at', None)
            result.append({
                "id": getattr(user, 'id', ''),
                "email": getattr(user, 'email', ''),
                "remind_time": getattr(user, 'remind_time', ''),
                "given_name": getattr(user, 'given_name', ''),
                "family_name": getattr(user, 'family_name', ''),
                "created_at": created_at_value.isoformat() if created_at_value else None
            })
        
        return {
            "status": "success",
            "total_users": len(result),
            "users": result
        }
    except Exception as e:
        logger.error(f"Error getting users with reminders: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get users: {str(e)}"
        }

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
    
    admin_password = getattr(admin, 'password')
    if not verify_password(request.password, admin_password):
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
    
    setattr(user, 'email_verification_token', verification_token)
    setattr(user, 'email_verification_expires_at', expiration_time)
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

# 1.8e. Lấy thông tin profile user (bao gồm remind_time)
@app.get("/api/v1/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile info including remind_time"""
    return {
        "id": getattr(current_user, 'id', None),
        "email": getattr(current_user, 'email', None),
        "name": getattr(current_user, 'given_name', None) or getattr(current_user, 'email', None),
        "avatar_url": getattr(current_user, 'avatar_url', None),
        "remind_time": getattr(current_user, 'remind_time', None),
        "total_courses": getattr(current_user, 'total_courses', None),
        "completed_courses": getattr(current_user, 'completed_courses', None),
        "total_quizzes": getattr(current_user, 'total_quizzes', None),
        "average_score": getattr(current_user, 'average_score', None),
        "study_streak": getattr(current_user, 'study_streak', None),
        "total_study_time": getattr(current_user, 'total_study_time', None),
        "is_email_verified": getattr(current_user, 'is_email_verified', None),
        "is_active": getattr(current_user, 'is_active', None)
    }

# TEST ONLY: Trigger study reminder email for a specific email (for manual testing)
# @app.post("/api/v1/test/send-reminder/{email}")
# async def test_send_reminder(email: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         return {"status": "error", "message": f"User {email} not found"}
#     if not getattr(user, 'is_email_verified', False) or not getattr(user, 'is_active', False):
#         return {"status": "error", "message": f"User {email} is not active or not verified"}
#     # Gửi email nhắc nhở học tập
#     user_email = getattr(user, 'email', None)
#     remind_time = getattr(user, 'remind_time', None) or "(chưa đặt)"
#     given_name = getattr(user, 'given_name', user_email)
#     send_email(
#         str(user_email),
#         "[Test] Nhắc nhở học tập PathLight",
#         f"Chào {given_name}, đây là email test nhắc nhở học tập của bạn! Thời gian nhắc: {remind_time}"
#     )
#     return {"status": "success", "message": f"Đã gửi email test nhắc nhở cho {user_email}"}

# TEST ONLY: Đổi remind_time cho user bằng API (dùng cho kiểm thử tự động)
@app.post("/api/v1/test/set-remind-time/{email}/{remind_time}")
async def test_set_remind_time(email: str, remind_time: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "error", "message": f"User {email} not found"}
    setattr(user, 'remind_time', remind_time)
    db.commit()
    return {"status": "success", "message": f"Đã đổi remind_time của {email} thành {remind_time}"}
