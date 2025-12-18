"""Database models for User Service (aligned with auth-service tables)."""

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
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=True)  # nullable for OAuth flows
    google_id = Column(String, nullable=True, unique=True)
    given_name = Column(String, nullable=True)
    family_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    dob = Column(DateTime(timezone=True), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    current_exp = Column(BigInteger, nullable=False, default=0)
    require_exp = Column(BigInteger, nullable=False, default=10)
    remind_time = Column(DateTime(timezone=True), nullable=True)
    sex = Column(Boolean, nullable=True)
    bio = Column(Text, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    activities = relationship("LearningActivity", back_populates="user", cascade="all, delete-orphan")

    @property
    def subscription(self) -> int:
        # placeholder for compatibility; subscription not stored in auth table
        return 0


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


__all__ = ["User", "LearningActivity", "Admin", "Base"]
