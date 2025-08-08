from sqlalchemy.orm import Session
from typing import Optional
from models import User
from config import config

def create_user(db: Session, email: str, password: str, **kwargs) -> User:
    user = User(email=email, password=password, **kwargs)
    db.add(user)
    db.commit()
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def update_user(db: Session, user_id: str, update_data: dict) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in update_data.items():
            setattr(user, key, value)
        db.commit()
        return user
    return None

def delete_user(db: Session, user_id: str) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
