import os
from dotenv import load_dotenv
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    # Expect a full SQLAlchemy URL string, e.g. postgresql+psycopg2://user:pass@host:5432/db
    url = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("PG_DSN")
        or ""
    )
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set; cannot persist course data."
        )
    return url


_engine = None
SessionLocal = None


def init_engine() -> None:
    # Load env lazily so .env is respected in local runs
    load_dotenv()
    global _engine, SessionLocal
    if _engine is None:
        _engine = create_engine(_database_url(), pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_db() -> Generator:
    init_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    """Create tables if not exist."""
    init_engine()
    # late import to avoid circular
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=_engine)
