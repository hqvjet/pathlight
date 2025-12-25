"""Ranking & leaderboard related logic extracted from user_controller."""
import logging
from sqlalchemy.orm import Session
from typing import List, Dict
from models import User, UserProfile
from config import config

logger = logging.getLogger(__name__)

__all__ = ["calculate_user_rank", "get_leaderboard_data", "get_users_by_ids"]

def calculate_user_rank(current_user: User, db: Session) -> dict:
    try:
        users = (
            db.query(User)
            .outerjoin(UserProfile, User.profile_id == UserProfile.profile_id)
            .filter(User.is_active == True)  # noqa: E712
            .order_by(UserProfile.current_exp.desc().nullslast())
            .all()
        )
        user_rank = 1
        total_users = len(users)
        for i, user in enumerate(users):
            if user.id == current_user.id:
                user_rank = i + 1
                break
        return {"rank": user_rank, "total_users": total_users}
    except Exception as e:  # pragma: no cover
        logger.error(f"Error calculating user rank: {e}")
        return {"rank": 1, "total_users": 1}

def _build_avatar_url(user: User) -> str | None:
    avatar_id = getattr(user, 'avatar_url', None)
    if not avatar_id:
        return f"{config.BASE_URL}/user/avatar?user-id={user.id}"  # will fallback to gender/default
    if avatar_id.startswith('http'):
        # If already contains user-id query keep as is else append
        return avatar_id if 'user-id=' in avatar_id else f"{avatar_id}?user-id={user.id}"
    # Internal stored key -> use public endpoint with user-id
    return f"{config.BASE_URL}/user/avatar?user-id={user.id}"

def get_leaderboard_data(db: Session, limit: int = 10) -> list:
    try:
        # Join with UserProfile to get correct exp ordering
        top_users = (
            db.query(User)
            .outerjoin(UserProfile, User.profile_id == UserProfile.profile_id)
            .filter(User.is_active == True)  # noqa: E712
            .order_by(UserProfile.current_exp.desc().nullslast())
            .limit(limit)
            .all()
        )
        leaderboard = []
        for i, user in enumerate(top_users):
            avatar_url = _build_avatar_url(user)
            initials = ''.join([name[0].upper() for name in [user.family_name or '', user.given_name or ''] if name])[:2] or user.email[0].upper()
            leaderboard.append({
                "rank": i + 1,
                "id": str(user.id),
                "name": f"{user.family_name or ''} {user.given_name or ''}".strip() or user.email.split('@')[0],
                "level": user.level or 1,
                "experience": user.current_exp or 0,
                "avatar_url": avatar_url,
                "initials": initials
            })
        return leaderboard
    except Exception as e:  # pragma: no cover
        logger.error(f"Error getting leaderboard: {e}")
        return []

def get_users_by_ids(user_ids: list[str], db: Session) -> dict:
    try:
        users = db.query(User).filter(User.id.in_(user_ids), User.is_active == True).all()  # noqa: E712
        data: Dict[str, dict] = {}
        for user in users:
            avatar_url = _build_avatar_url(user)
            initials = ''.join([name[0].upper() for name in [user.family_name or '', user.given_name or ''] if name])[:2] or user.email[0].upper()
            data[str(user.id)] = {
                "id": str(user.id),
                "name": f"{user.family_name or ''} {user.given_name or ''}".strip() or user.email.split('@')[0],
                "avatar_url": avatar_url,
                "level": user.level or 1,
                "initials": initials
            }
        return data
    except Exception as e:  # pragma: no cover
        logger.error(f"Error getting users by IDs: {e}")
        return {}
