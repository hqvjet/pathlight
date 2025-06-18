from sqlalchemy import Column, String, DateTime, Integer, Boolean, BigInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base


class User(Base):
    __tablename__ = "user"
    
    user_id = Column(String, primary_key=True)
    profile_id = Column(String, ForeignKey("user_profile.profile_id"), nullable=False)
    email = Column(String, nullable=True)
    password = Column(String, nullable=True)
    google_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    profile = relationship("UserProfile", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profile"
    
    profile_id = Column(String, primary_key=True)
    family_name = Column(String, nullable=False)
    given_name = Column(String, nullable=True)
    avatar_id = Column(String, nullable=False)
    dob = Column(DateTime, nullable=False)
    level = Column(Integer, nullable=False, default=1)
    current_exp = Column(BigInteger, nullable=False, default=0)
    require_exp = Column(BigInteger, nullable=False, default=10)
    remind_time = Column(DateTime, nullable=False)
    sex = Column(Boolean, nullable=False)
    bio = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="profile", uselist=False)
