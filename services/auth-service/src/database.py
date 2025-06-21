# db/database.py

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from .config import DATABASE_URL, DEBUG

# Create engine
engine = create_engine(DATABASE_URL, echo=DEBUG)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()
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

# Create tables from Base subclasses
def create_tables():
    Base.metadata.create_all(bind=engine)
