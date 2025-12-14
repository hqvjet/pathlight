"""Database models for User Service."""

from __future__ import annotations

import uuid
from sqlalchemy import Column, String, DateTime, Integer, Boolean, BigInteger, Text, ForeignKey, event
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, object_session


Base = declarative_base()


def _generate_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "user"

    id = Column("user_id", String, primary_key=True, default=_generate_id)
    profile_id = Column(String, ForeignKey("user_profile.profile_id"), nullable=True)

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

    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="joined",
    )
    activities = relationship("LearningActivity", back_populates="user", cascade="all, delete-orphan")

    # ---- Profile proxies -------------------------------------------------
    def _ensure_profile(self):
        if not self.profile:
            self.profile = UserProfile(profile_id=_generate_id())
        return self.profile

    @property
    def family_name(self) -> str | None:
        return getattr(self._ensure_profile(), "family_name", None)

    @family_name.setter
    def family_name(self, value: str | None):
        self._ensure_profile().family_name = value

    @property
    def given_name(self) -> str | None:
        return getattr(self._ensure_profile(), "given_name", None)

    @given_name.setter
    def given_name(self, value: str | None):
        self._ensure_profile().given_name = value

    @property
    def avatar_url(self) -> str | None:
        return getattr(self._ensure_profile(), "avatar_url", None)

    @avatar_url.setter
    def avatar_url(self, value: str | None):
        self._ensure_profile().avatar_url = value

    @property
    def dob(self):
        return getattr(self._ensure_profile(), "dob", None)

    @dob.setter
    def dob(self, value):
        self._ensure_profile().dob = value

    @property
    def level(self) -> int:
        return getattr(self._ensure_profile(), "level", 1)

    @level.setter
    def level(self, value: int):
        self._ensure_profile().level = value

    @property
    def current_exp(self) -> int:
        return getattr(self._ensure_profile(), "current_exp", 0)

    @current_exp.setter
    def current_exp(self, value: int):
        self._ensure_profile().current_exp = value

    @property
    def require_exp(self) -> int:
        return getattr(self._ensure_profile(), "require_exp", 10)

    @require_exp.setter
    def require_exp(self, value: int):
        self._ensure_profile().require_exp = value

    @property
    def remind_time(self):
        return getattr(self._ensure_profile(), "remind_time", None)

    @remind_time.setter
    def remind_time(self, value):
        self._ensure_profile().remind_time = value

    @property
    def sex(self):
        return getattr(self._ensure_profile(), "sex", None)

    @sex.setter
    def sex(self, value):
        self._ensure_profile().sex = value

    @property
    def bio(self) -> str | None:
        return getattr(self._ensure_profile(), "bio", None)

    @bio.setter
    def bio(self, value: str | None):
        self._ensure_profile().bio = value


class UserProfile(Base):
    __tablename__ = "user_profile"

    profile_id = Column(String, primary_key=True, default=_generate_id)
    family_name = Column(String, nullable=True)
    given_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    dob = Column(DateTime(timezone=True), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    current_exp = Column(BigInteger, nullable=False, default=0)
    require_exp = Column(BigInteger, nullable=False, default=10)
    remind_time = Column(DateTime(timezone=True), nullable=True)
    sex = Column(Boolean, nullable=True)
    bio = Column(Text, nullable=True)

    user = relationship("User", back_populates="profile", uselist=False)


@event.listens_for(User, "before_insert")
def _ensure_profile_before_insert(mapper, connection, target: User):  # pragma: no cover - covered indirectly in tests
    """Guarantee every user has a profile row before insert for consistent proxies."""
    target._ensure_profile()
    if target.profile:
        target.profile_id = target.profile.profile_id
        sess = object_session(target)
        if sess and target.profile not in sess:
            sess.add(target.profile)


class LearningActivity(Base):
    __tablename__ = "learning_activity"

    id = Column("activity_id", String, primary_key=True, default=_generate_id)
    user_id = Column(String, ForeignKey("user.user_id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    date_of_the_week = Column(String, nullable=False)
    count = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="activities")


class Admin(Base):
    """Admin model for managing privileged users."""

    __tablename__ = "admin"

    id = Column("admin_id", String, primary_key=True, default=_generate_id)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)


__all__ = ["User", "UserProfile", "LearningActivity", "Admin", "Base"]
