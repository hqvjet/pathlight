from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import re

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    google_id: Optional[str] = None

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
    credential: Optional[str] = None  # Google ID token for verification

class AdminSigninRequest(BaseModel):
    username: str
    password: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    status: int
    message: Optional[str] = None

class AuthResponse(BaseModel):
    status: int
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    message: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserInfoResponse(BaseModel):
    status: int
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_email_verified: Optional[bool] = None
