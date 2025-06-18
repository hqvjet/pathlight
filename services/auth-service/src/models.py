from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from src.database import Base


class Admin(Base):
    __tablename__ = "admin"
    
    admin_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
