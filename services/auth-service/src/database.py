# db/database.py

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Import local config and models
from .config import get_database_url, get_debug_mode
from .models import Base

# Database configuration
DATABASE_URL = get_database_url()
DEBUG = get_debug_mode()

# Create engine
engine = create_engine(DATABASE_URL, echo=DEBUG)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use the Base from models
metadata = Base.metadata

# FastAPI-compatible dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Context manager for CLI/scripts
@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
