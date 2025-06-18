from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - sẽ được config từ environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quiz.db")

# Lazy loading để tránh lỗi khi import models
def get_engine():
    return create_engine(DATABASE_URL)

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

Base = declarative_base()
metadata = Base.metadata
