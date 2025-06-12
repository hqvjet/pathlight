from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(current_user=Depends(get_current_user)):
    return UserRead(
        user_id=current_user.user_id,
        email=current_user.email,
        first_name=current_user.profile.first_name,
        last_name=current_user.profile.last_name,
        dob=current_user.profile.dob,
        sex=current_user.profile.sex,
    )
