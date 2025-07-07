from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import re

class ChangeInfoRequest(BaseModel):
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    dob: Optional[datetime] = None
    sex: Optional[str] = None
    bio: Optional[str] = None
    
    @validator('sex')
    def validate_sex(cls, v):
        if v and v not in ['Male', 'Female', 'Other']:
            raise ValueError('Sex must be Male, Female, or Other')
        return v

class NotifyTimeRequest(BaseModel):
    remind_time: str
    
    @validator('remind_time')
    def validate_time_format(cls, v):
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format (e.g., "18:30")')
        return v

class UserInfoResponse(BaseModel):
    status: int
    Info: Optional[dict] = None
    message: Optional[str] = None

class MessageResponse(BaseModel):
    status: int
    message: Optional[str] = None

class DashboardResponse(BaseModel):
    status: int
    info: Optional[dict] = None
    message: Optional[str] = None

class UsersListResponse(BaseModel):
    status: int
    infos: Optional[list] = None
    message: Optional[str] = None
