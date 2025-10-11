import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import Admin


def hash_password(password: str, rounds: int = 12) -> str:
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode(), salt).decode()


def create_admin(db: Session, username: str, password: str) -> Admin:
    admin = Admin(username=username, password=hash_password(password))
    db.add(admin)
    try:
        db.commit()
        db.refresh(admin)
    except IntegrityError:
        db.rollback()
        raise
    return admin


def get_admin_by_username(db: Session, username: str) -> Admin | None:
    return db.query(Admin).filter(Admin.username == username).first()
