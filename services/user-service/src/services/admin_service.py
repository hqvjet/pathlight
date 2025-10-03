import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Admin

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"

logger = logging.getLogger(__name__)


@contextmanager
def _get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def ensure_default_admin_account() -> bool:
    """Ensure there is at least one admin account with default credentials.

    Returns True if a new admin was created, False if it already existed.
    Raises SQLAlchemyError if a database error occurs.
    """
    with _get_session() as session:
        try:
            existing = (
                session.query(Admin)
                .filter(Admin.username == DEFAULT_ADMIN_USERNAME)
                .first()
            )
            if existing:
                logger.debug("Default admin already present (id=%s)", existing.id)
                return False

            admin = Admin(username=DEFAULT_ADMIN_USERNAME, password=DEFAULT_ADMIN_PASSWORD)
            session.add(admin)
            session.commit()
            logger.info("Created default admin account with username '%s'", DEFAULT_ADMIN_USERNAME)
            return True
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Failed to ensure default admin account: %s", exc)
            raise


def create_admin_account(username: str, password: str, *, overwrite: bool = False) -> Admin:
    """Create a new admin account or optionally overwrite its password.

    Returns the created or updated ``Admin`` instance.
    Raises ``ValueError`` if the username exists and ``overwrite`` is ``False``.
    """
    if not username or not password:
        raise ValueError("Username and password are required")

    with _get_session() as session:
        try:
            admin = session.query(Admin).filter(Admin.username == username).one_or_none()

            if admin:
                if not overwrite:
                    raise ValueError(f"Admin '{username}' already exists")
                setattr(admin, "password", password)
                session.commit()
                session.refresh(admin)
                logger.info("Updated admin '%s' password", username)
                return admin

            new_admin = Admin(username=username, password=password)
            session.add(new_admin)
            session.commit()
            session.refresh(new_admin)
            logger.info("Created admin '%s'", username)
            return new_admin
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Failed to create admin '%s': %s", username, exc)
            raise
