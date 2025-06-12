from datetime import date
from uuid import UUID
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    first_name: str
    last_name: str
    dob: date
    sex: bool

class UserRead(UserBase):
    user_id: UUID
    first_name: str
    last_name: str
    dob: date
    sex: bool

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
