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
    profile_id = Column(String, ForeignKey("user_profile.profile_id", ondelete="CASCADE"), nullable=True)
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

    profile = relationship("UserProfile", back_populates="user", lazy="joined", cascade="all, delete-orphan", single_parent=True)
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
    def avatar_url(self):
        return getattr(self._p(), "avatar_url", None) if self._p() else None

    @avatar_url.setter
    def avatar_url(self, value):
        if self._p():
            setattr(self._p(), "avatar_url", value)
        else:
            try:
                from services.experience_service import get_exp_for_level 

                next_req = get_exp_for_level(2)
            except Exception:
                next_req = 10

            profile = UserProfile(
                profile_id=_generate_id(),
                subscription=0,
                streak=0,
                level=1,
                current_exp=0,
                require_exp=next_req,
            )
            setattr(self, "profile", profile)
            setattr(self, "profile_id", profile.profile_id)
            setattr(profile, "avatar_url", value)

    @property
    def avatar_id(self):
        return self.avatar_url

    @property
    def current_exp(self):
        return getattr(self._p(), "current_exp", 0) if self._p() else 0

    @current_exp.setter
    def current_exp(self, value):
        profile = self._ensure_profile()
        setattr(profile, "current_exp", value)

    @property
    def require_exp(self):
        try:
            from services.experience_service import get_exp_for_level 

            default_req = get_exp_for_level(2)
        except Exception:
            default_req = 10
        if self._p():
            return getattr(self._p(), "require_exp", default_req)
        return default_req

    @require_exp.setter
    def require_exp(self, value):
        profile = self._ensure_profile()
        setattr(profile, "require_exp", value)

    @property
    def remind_time(self):
        return getattr(self._p(), "remind_time", None) if self._p() else None

    @property
    def sex(self):
        return getattr(self._p(), "sex", None) if self._p() else None

    @property
    def bio(self):
        return getattr(self._p(), "bio", None) if self._p() else None

    @bio.setter
    def bio(self, value):
        profile = self._ensure_profile()
        setattr(profile, "bio", value)

    @property
    def streak(self):
        return getattr(self._p(), "streak", 0) if self._p() else 0

    @property
    def subscription(self):
        return getattr(self._p(), "subscription", 0) if self._p() else 0

    @property
    def level(self):
        return getattr(self._p(), "level", 1) if self._p() else 1

    @level.setter
    def level(self, value):
        profile = self._ensure_profile()
        setattr(profile, "level", value)

    def _ensure_profile(self):
        profile = getattr(self, "profile", None)
        if profile:
            return profile
        try:
            from services.experience_service import get_exp_for_level

            default_req = get_exp_for_level(2)
        except Exception:
            default_req = 10

        profile = UserProfile(
            profile_id=_generate_id(),
            subscription=0,
            streak=0,
            level=1,
            current_exp=0,
            require_exp=default_req,
        )
        setattr(self, "profile", profile)
        if not getattr(self, "profile_id", None):
            setattr(self, "profile_id", profile.profile_id)
        return profile


class UserProfile(Base):
    __tablename__ = "user_profile"

    profile_id = Column(String, primary_key=True, default=_generate_id)
    subscription = Column(Integer, nullable=False, default=0)
    family_name = Column(String, nullable=True)
    given_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
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
