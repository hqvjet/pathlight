"""
Database models for Auth Service
Self-contained models that don't depend on external libs
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, BigInteger, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

# Base for auth service models
Base = declarative_base()


class User(Base):
    """
    User model for auth service
    """
    __tablename__ = "users"
    
    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Authentication fields
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=True)  # Nullable for OAuth users
    is_email_verified = Column(Boolean, default=False)
    
    # Email verification fields
    email_verification_token = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset fields
    password_reset_token = Column(String, nullable=True)
    
    # OAuth fields
    google_id = Column(String, nullable=True, unique=True)
    given_name = Column(String, nullable=True)
    family_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # Profile fields
    dob = Column(DateTime(timezone=True), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    current_exp = Column(BigInteger, nullable=False, default=0)
    require_exp = Column(BigInteger, nullable=False, default=10)
    remind_time = Column(String, nullable=True)
    sex = Column(Boolean, nullable=True)
    bio = Column(Text, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)


class Admin(Base):
    """Admin model for authentication."""
    __tablename__ = "admins"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TokenBlacklist(Base):
    """Token blacklist for JWT invalidation."""
    __tablename__ = "token_blacklist"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String, nullable=False, unique=True, index=True)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


# Make all models available for import
__all__ = ['User', 'Admin', 'TokenBlacklist', 'Base']
