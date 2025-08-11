"""User repository: encapsulates all DB access for User model."""
from typing import Optional, Sequence, Iterable
from sqlalchemy.orm import Session
from models import User

__all__ = [
    "get_by_id",
    "get_by_email",
    "list_active",
    "list_active_ordered_by_exp",
    "list_active_by_ids",
    "commit",
]

def get_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def list_active(db: Session) -> Sequence[User]:
    return db.query(User).filter(User.is_active == True).all()  # noqa: E712

def list_active_ordered_by_exp(db: Session) -> Sequence[User]:
    return db.query(User).filter(User.is_active == True).order_by(User.current_exp.desc()).all()  # noqa: E712

def list_active_by_ids(db: Session, ids: Iterable[str]) -> Sequence[User]:
    return db.query(User).filter(User.id.in_(list(ids)), User.is_active == True).all()  # noqa: E712

def commit(db: Session):  # simple wrapper for future enhancements / events
    db.commit()
