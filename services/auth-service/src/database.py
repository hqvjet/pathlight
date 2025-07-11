# db/database.py

from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Import local config and models
from .config import get_database_url, get_debug_mode
from .models import Base

# Database configuration
DATABASE_URL = get_database_url()
DEBUG = get_debug_mode()

# Create engine with improved connection settings
engine = create_engine(
    DATABASE_URL, 
    echo=DEBUG,
    pool_pre_ping=True, 
    pool_recycle=3600,   
    pool_size=10,       
    max_overflow=20,    
    connect_args={
        "connect_timeout": 10,
        "application_name": "pathlight_auth_service"
    }
)

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
    """Create all tables with retry mechanism"""
    # Import all models to ensure they're registered
    from .models import User, Admin, TokenBlacklist, Base
    import time
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Test connection first
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create tables with explicit transaction
            with engine.begin() as conn:
                Base.metadata.create_all(bind=conn)
            
            print(f"Database tables created successfully (attempt {attempt + 1})")
            return
            
        except Exception as e:
            print(f"Error creating tables (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Failed to create tables after all retries")
                raise

def check_tables_exist():
    """Check if required tables exist in the database"""
    try:
        with engine.connect() as conn:
            # Check if tables exist using inspector
            inspector = inspect(conn)
            table_names = inspector.get_table_names()
            required_tables = ['users', 'admins', 'token_blacklist']
            existing_tables = set(table_names)
            missing_tables = set(required_tables) - existing_tables
            
            if missing_tables:
                print(f"Missing tables: {missing_tables}")
                return False
            else:
                print(f"All required tables exist: {required_tables}")
                return True
                
    except Exception as e:
        print(f"Error checking tables: {e}")
        return False

def ensure_tables():
    """Ensure tables exist, create if missing"""
    if not check_tables_exist():
        print("🔧 Creating missing tables...")
        create_tables()
    else:
        print("Tables already exist, skipping creation")
