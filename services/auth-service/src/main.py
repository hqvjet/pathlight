from fastapi import FastAPI, HTTPException, Depends, status, Response, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import bcrypt
import jwt
import os
import secrets
import uuid
from datetime import datetime, timedelta
import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.database import get_db, create_tables
from src.models import User, Admin, TokenBlacklist

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
security = HTTPBearer()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pathlight-super-secret-key-2025")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "pathlight-refresh-secret-key-2025")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@pathlight.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

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
    message: str = None

class AuthResponse(BaseModel):
    status: int
    access_token: str

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP"""
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("Email credentials not configured. Skipping email send.")
            return
            
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, to_email, text)
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")

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

# 1.1. Đăng ký
@app.post("/api/v1/signup", response_model=MessageResponse)
async def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    """User registration endpoint"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        return MessageResponse(status=401, message="Tài khoản này đã được sử dụng")
    
    # Create new user
    verification_token = generate_token()
    hashed_password = hash_password(user_data.password)
    
    user = User(
        email=user_data.email,
        password=hashed_password,
        email_verification_token=verification_token,
        is_email_verified=False
    )
    
    db.add(user)
    db.commit()
    
    # Send verification email
    verification_link = f"{FRONTEND_URL}/api/v1/verify-email?token={verification_token}"
    email_body = f"""
    <html>
    <body>
        <h2>Xác thực tài khoản</h2>
        <p>Chào bạn,</p>
        <p>Vui lòng click vào link dưới đây để xác thực tài khoản của bạn:</p>
        <a href="{verification_link}">Xác thực tài khoản</a>
        <p>Link này sẽ hết hạn sau 24 giờ.</p>
    </body>
    </html>
    """
    
    send_email(user_data.email, "Xác thực tài khoản", email_body)
    
    return MessageResponse(status=200, message="Mã xác thực đã được gửi vào email của bạn, xin vui lòng xác thực email của bạn")

# 1.2. Xác thực Email
@app.get("/api/v1/verify-email", response_model=MessageResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email endpoint"""
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        return MessageResponse(status=401, message="Token đã hết hạn, xin vui lòng đăng ký lại")
    
    # Update user as verified
    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()
    
    return MessageResponse(status=200)

# 1.3. Đăng nhập
@app.post("/api/v1/signin", response_model=AuthResponse)
async def signin(user_data: SigninRequest, db: Session = Depends(get_db)):
    """User login endpoint"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        return AuthResponse(status=401, message="Sai mật khẩu, xin vui lòng thử lại")
    
    if not user.password or not verify_password(user_data.password, user.password):
        return AuthResponse(status=401, message="Sai mật khẩu, xin vui lòng thử lại")
    
    if not user.is_email_verified:
        return AuthResponse(status=401, message="Email chưa được xác thực")
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return AuthResponse(status=200, access_token=access_token)

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
        return MessageResponse(status=401, message="Tài khoản không tồn tại, xin vui lòng thử lại")
    
    # Generate reset token
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
        <p>Link này sẽ hết hạn sau 1 giờ.</p>
    </body>
    </html>
    """
    
    send_email(request.email, "Đặt lại mật khẩu", email_body)
    
    return MessageResponse(status=200, message="Xin vui lòng kiểm tra email của bạn để reset mật khẩu")

# 1.6. Đặt lại mật khẩu
@app.post("/api/v1/reset-password/{token}", response_model=MessageResponse)
async def reset_password(token: str, request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password endpoint"""
    user = db.query(User).filter(User.password_reset_token == token).first()
    if not user:
        return MessageResponse(status=401, message="Token đã hết hạn, xin vui lòng thử lại")
    
    # Check if new password is same as old password
    if user.password and verify_password(request.new_password, user.password):
        return MessageResponse(status=401, message="Mật khẩu bạn vừa nhập giống với mật khẩu cũ, xin vui lòng thử lại")
    
    # Update password
    user.password = hash_password(request.new_password)
    user.password_reset_token = None
    db.commit()
    
    return MessageResponse(status=200)

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
        return AuthResponse(status=401, message="Có lỗi xảy ra, xin vui lòng thử lại")

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
        return AuthResponse(status=401, message="Sai mật khẩu, xin vui lòng thử lại")
    
    if not verify_password(request.password, admin.password):
        return AuthResponse(status=401, message="Sai mật khẩu, xin vui lòng thử lại")
    
    # Create access token with admin role
    access_token = create_access_token(data={"sub": admin.id, "role": "admin"})
    
    return AuthResponse(status=200, access_token=access_token)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
