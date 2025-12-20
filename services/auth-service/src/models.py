"""Database models for Auth Service (shared tables)."""

from sqlalchemy import Column, String, DateTime, Boolean, BigInteger, Integer, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, nullable=True)  # FK to user_profile in shared schema
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String, nullable=True)
    google_id = Column(String, nullable=True, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)


class UserProfile(Base):
    __tablename__ = "user_profile"

    profile_id = Column(String, primary_key=True)
    subscription = Column(Integer, nullable=False, default=0)
    family_name = Column(String, nullable=True)
    given_name = Column(String, nullable=True)
    avatar_id = Column(String, nullable=True)
    dob = Column(DateTime(timezone=True), nullable=True)
    streak = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)
    current_exp = Column(BigInteger, nullable=False, default=0)
    require_exp = Column(BigInteger, nullable=False, default=10)
    remind_time = Column(DateTime(timezone=True), nullable=True)
    sex = Column(Boolean, nullable=True)
    bio = Column(Text, nullable=True)


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


__all__ = ['User', 'UserProfile', 'Admin', 'TokenBlacklist', 'Base']
