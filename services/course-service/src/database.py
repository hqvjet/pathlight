import sys
import os

# Add libs path to use common utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'libs', 'common-utils-py', 'src'))

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlight_common import get_database_url, get_debug_mode

# Database configuration from common utilities
DATABASE_URL = get_database_url()
DEBUG = get_debug_mode()

# Create engine
engine = create_engine(DATABASE_URL, echo=DEBUG)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()
metadata = Base.metadata
