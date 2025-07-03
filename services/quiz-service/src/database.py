import sys
import os

# Add libs path to use common utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'libs', 'common-utils-py', 'src'))

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlight_common import get_database_url, get_debug_mode

# Database configuration from common utilities
DATABASE_URL = get_database_url()
DEBUG = get_debug_mode()

# Lazy loading để tránh lỗi khi import models
def get_engine():
    return create_engine(DATABASE_URL, echo=DEBUG)

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

Base = declarative_base()
metadata = Base.metadata
