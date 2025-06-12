from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User, UserProfile

async def get_user_by_email(db: AsyncSession, email: str):
    res = await db.execute(select(User).where(User.email == email))
    return res.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str):
    res = await db.execute(select(User).where(User.user_id == user_id))
    return res.scalars().first()

async def create_user(db: AsyncSession, *, email: str, password: str, first_name: str, last_name: str, dob, sex: bool):
    from ..core.security import hash_password
    profile = UserProfile(first_name=first_name, last_name=last_name, dob=dob, sex=sex)
    user = User(email=email, password=hash_password(password), profile=profile)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
