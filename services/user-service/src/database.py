from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from config import get_database_url, get_debug_mode

logger = logging.getLogger(__name__)

DATABASE_URL = get_database_url()
DEBUG = get_debug_mode()

engine = create_engine(
    DATABASE_URL, 
    echo=DEBUG,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    try:
        from models import Base
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def drop_tables():
    try:
        from .models import Base
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped")
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        raise


def reset_database():
    logger.warning("Resetting database...")
    drop_tables()
    create_tables()
    logger.info("Database reset completed")
