from sqlalchemy import Column, String, Boolean, Date, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base

class UserProfile(Base):
    __tablename__ = "user_profile"
    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String)
    last_name = Column(String)
    dob = Column(Date, nullable=False)
    level = Column(Integer, nullable=False, default=1)
    current_exp = Column(Integer, nullable=False, default=0)
    sex = Column(Boolean, nullable=False)
    bio = Column(String)
    user = relationship("User", back_populates="profile", uselist=False)

class User(Base):
    __tablename__ = "user"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profile.profile_id", ondelete="CASCADE"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    profile = relationship("UserProfile", back_populates="user")

class Admin(Base):
    __tablename__ = "admin"
    admin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
