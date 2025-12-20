"""Database models for User Service (shared users + profile tables)."""

from __future__ import annotations

import uuid
from sqlalchemy import Column, String, DateTime, Integer, Boolean, BigInteger, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


def _generate_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_generate_id)
    profile_id = Column(String, ForeignKey("user_profile.profile_id", ondelete="SET NULL"), nullable=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=True)  # nullable for OAuth flows
    google_id = Column(String, nullable=True, unique=True)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    profile = relationship("UserProfile", back_populates="user", lazy="joined")
    activities = relationship("LearningActivity", back_populates="user", cascade="all, delete-orphan")

    # Proxy properties to profile for compatibility with existing code
    def _p(self):
        return self.profile

    @property
    def family_name(self):
        return getattr(self._p(), "family_name", None) if self._p() else None

    @property
    def given_name(self):
        return getattr(self._p(), "given_name", None) if self._p() else None

    @property
    def avatar_id(self):
        return getattr(self._p(), "avatar_id", None) if self._p() else None

    @property
    def level(self):
        return getattr(self._p(), "level", 1) if self._p() else 1

    @property
    def current_exp(self):
        return getattr(self._p(), "current_exp", 0) if self._p() else 0

    @property
    def require_exp(self):
        return getattr(self._p(), "require_exp", 10) if self._p() else 10

    @property
    def remind_time(self):
        return getattr(self._p(), "remind_time", None) if self._p() else None

    @property
    def sex(self):
        return getattr(self._p(), "sex", None) if self._p() else None

    @property
    def bio(self):
        return getattr(self._p(), "bio", None) if self._p() else None

    @property
    def streak(self):
        return getattr(self._p(), "streak", 0) if self._p() else 0

    @property
    def subscription(self):
        return getattr(self._p(), "subscription", 0) if self._p() else 0


class UserProfile(Base):
    __tablename__ = "user_profile"

    profile_id = Column(String, primary_key=True, default=_generate_id)
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

    user = relationship("User", back_populates="profile", uselist=False)


class LearningActivity(Base):
    __tablename__ = "learning_activity"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    date = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    count = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="activities")


class Admin(Base):
    """Admin model aligned to auth-service admins table."""

    __tablename__ = "admins"

    id = Column(String, primary_key=True, default=_generate_id)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


__all__ = ["User", "UserProfile", "LearningActivity", "Admin", "Base"]
