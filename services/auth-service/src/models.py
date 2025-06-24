import sys
import os

# Add libs path to use shared models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs', 'common-types-py'))

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from src.database import Base
import uuid

# Import shared User model
from shared_models import User

# Auth-service specific models
class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token_jti = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Make shared User model available
__all__ = ['User', 'Admin', 'TokenBlacklist']
