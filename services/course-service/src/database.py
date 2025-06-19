from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - đọc từ environment variables
DATABASE_URL = os.getenv("COURSE_DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://postgres:1210@localhost:5432/pathlight"))

# Create engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()
metadata = Base.metadata
