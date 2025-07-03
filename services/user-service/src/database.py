from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import local config and models
from .config import get_database_url, get_debug_mode
from .models import Base, User

# Database configuration
DATABASE_URL = get_database_url()
DEBUG = get_debug_mode()

# Create engine
engine = create_engine(DATABASE_URL, echo=DEBUG)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use the Base from models
metadata = Base.metadata

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

metadata = Base.metadata

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()
metadata = Base.metadata
