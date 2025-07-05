"""
Database configuration for Pathlight User Service
Standalone database setup without external dependencies
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Import local config
from .config import get_database_url, get_debug_mode

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = get_database_url()
DEBUG = get_debug_mode()

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL, 
    echo=DEBUG,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Database dependency for FastAPI
    Provides database session for each request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    try:
        # Import models to ensure they're registered
        from .models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {str(e)}")
        raise


def drop_tables():
    """Drop all database tables (for testing/reset)"""
    try:
        from .models import Base
        Base.metadata.drop_all(bind=engine)
        logger.info("⚠️ All database tables dropped")
        
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {str(e)}")
        raise


def reset_database():
    """Reset database by dropping and recreating tables"""
    logger.warning("🔄 Resetting database...")
    drop_tables()
    create_tables()
    logger.info("✅ Database reset completed")
