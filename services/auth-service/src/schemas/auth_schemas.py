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
    message: Optional[str] = None
