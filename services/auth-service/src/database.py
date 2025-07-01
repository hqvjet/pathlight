# db/database.py

import sys
import os

# Add libs path to use common utilities
sys.path.insert(0, '/app/libs/common-utils-py/src')
# Add libs path for shared models
sys.path.insert(0, '/app/libs/common-types-py')

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from pathlight_common import get_database_url, get_debug_mode

# Database configuration from common utilities
DATABASE_URL = get_database_url()
DEBUG = get_debug_mode()

# Create engine
engine = create_engine(DATABASE_URL, echo=DEBUG)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import shared models to get the SharedBase
from shared_models import SharedBase

# Use SharedBase as our Base for this service
Base = SharedBase
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
