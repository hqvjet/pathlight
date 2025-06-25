"""
Shared database models for PathLight services.
This module contains models that are shared across multiple services.
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, BigInteger, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

# Base for shared models
SharedBase = declarative_base()


class User(SharedBase):
    """
    Unified User model that serves both auth-service and user-service needs.
    This is the single source of truth for user data.
    """
    __tablename__ = "users"
    
    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Authentication fields (used by auth-service)
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
    
    # Profile fields (used by user-service)
    dob = Column(DateTime(timezone=True), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    current_exp = Column(BigInteger, nullable=False, default=0)
    require_exp = Column(BigInteger, nullable=False, default=10)
    remind_time = Column(DateTime(timezone=True), nullable=True)
    sex = Column(Boolean, nullable=True)  # True for male, False for female
    bio = Column(Text, nullable=True)
    avatar_id = Column(String, nullable=True)  # Added to match database
    
    # Common fields
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Admin(SharedBase):
    """Admin model for authentication."""
    __tablename__ = "admins"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TokenBlacklist(SharedBase):
    """Token blacklist for JWT invalidation."""
    __tablename__ = "token_blacklist"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token_jti = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
