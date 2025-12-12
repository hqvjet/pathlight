"""
Database models for User Service
Self-contained models that don't depend on external libs
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, BigInteger, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

# Base for user service models
Base = declarative_base()

class User(Base):
    """User table matching ERD (user + profile split)."""

    __tablename__ = "user"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, ForeignKey("user_profile.profile_id"), nullable=False)

    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=True)  # nullable for OAuth
    google_id = Column(String, nullable=True, unique=True)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    activities = relationship("LearningActivity", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profile"

    profile_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    family_name = Column(String, nullable=True)
    given_name = Column(String, nullable=True)
    avatar_id = Column(String, nullable=True)
    dob = Column(DateTime(timezone=True), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    current_exp = Column(BigInteger, nullable=False, default=0)
    require_exp = Column(BigInteger, nullable=False, default=10)
    remind_time = Column(DateTime(timezone=True), nullable=True)
    sex = Column(Boolean, nullable=True)
    bio = Column(Text, nullable=True)

    user = relationship("User", back_populates="profile", uselist=False)


class LearningActivity(Base):
    __tablename__ = "learning_activity"

    activity_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user.user_id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    date_of_the_week = Column(String, nullable=False)
    count = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="activities")


class Admin(Base):
    """Admin model for managing privileged users"""

    __tablename__ = "admin"

    admin_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)


# Make all models available for import
__all__ = ['User', 'UserProfile', 'LearningActivity', 'Admin', 'Base']
