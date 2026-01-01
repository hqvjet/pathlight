"""Experience & Level progression logic for User Service.
Separated from monolithic user_controller for clarity & testability.
"""
from __future__ import annotations
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import User
from config import config
from services.ranking_service import calculate_user_rank
from services.token_service import create_access_token

logger = logging.getLogger(__name__)

__all__ = [
    "LEVEL_EXP_THRESHOLDS",
    "get_exp_for_level",
    "calculate_level_from_exp",
    "auto_level_up",
    "require_exp_for_level",
    "update_test_stats",
    "reset_test_stats",
    "simulate_learning_activity",
    "add_experience",
    "get_level_system_info",
]

# ===== LEVEL SYSTEM CONFIGURATION =====
LEVEL_EXP_THRESHOLDS = [
    0,
    1000,
    3000,
    6000,
    10000,
    15000,
    21000,
    28000,
    36000,
    45000,
    55000,
    66000,
    78000,
    91000,
    105000,
    120000,
    136000,
    153000,
    171000,
    190000,
    210000,
    231000,
    253000,
    276000,
    300000,
    325000,
    351000,
    378000,
    406000,
    435000,
    465000,
    496000,
    528000,
    561000,
    595000,
    630000,
    666000,
    703000,
    741000,
    780000,
    820000,
    861000,
    903000,
    946000,
    990000,
    1035000,
    1081000,
    1128000,
    1176000,
    1225000,
    1275000,
    1326000,
    1378000,
    1431000,
    1485000,
    1540000,
    1596000,
    1653000,
    1711000,
    1770000,
    1830000,
    1891000,
    1953000,
    2016000,
    2080000,
    2145000,
    2211000,
]

def get_exp_for_level(level: int) -> int:
    if level <= 1:
        return 0
    idx = level - 1
    if idx < len(LEVEL_EXP_THRESHOLDS):
        return LEVEL_EXP_THRESHOLDS[idx]
    base_level = len(LEVEL_EXP_THRESHOLDS)
    base_exp = LEVEL_EXP_THRESHOLDS[-1]
    growth_factor = 1.3
    additional_levels = level - base_level
    additional_exp = base_exp * (growth_factor ** additional_levels) - base_exp
    return int(base_exp + additional_exp)

def calculate_level_from_exp(current_exp: int) -> Tuple[int, int, int]:
    if current_exp <= 0:
        return 1, 0, get_exp_for_level(2)
    level = 1
    while True:
        next_level_exp = get_exp_for_level(level + 1)
        if current_exp < next_level_exp:
            break
        level += 1
        if level > 1000:  # safety cap
            break
    current_level_exp = get_exp_for_level(level)
    next_level_exp = get_exp_for_level(level + 1)
    return level, current_level_exp, next_level_exp


def require_exp_for_level(level: int) -> int:
    """Derived required exp to reach next level (level+1)."""
    next_level = level + 1
    return get_exp_for_level(next_level)

def auto_level_up(current_exp: int, current_level: Optional[int] = None) -> Tuple[int, int, bool]:
    new_level, _, next_level_exp = calculate_level_from_exp(current_exp)
    level_increased = current_level is not None and new_level > current_level
    return new_level, next_level_exp, level_increased

# ---------- Test / Simulation Utilities (originally test APIs) ----------
from schemas.user_schemas import TestStatsRequest, TestStatsResponse, UpdatedStats  # type: ignore

async def update_test_stats(request: TestStatsRequest, current_user: User, db: Session) -> TestStatsResponse:
    try:
        current_level_val = getattr(current_user, 'level', 1)
        original_stats = {
            "level": current_level_val,
            "current_exp": getattr(current_user, 'current_exp', 0),
            "require_exp": getattr(current_user, 'require_exp', require_exp_for_level(current_level_val)),
        }
        calculated_exp = 0
        if request.current_exp is not None:
            calculated_exp = request.current_exp
        else:
            if request.completed_courses:
                calculated_exp += request.completed_courses * 100
            if request.completed_quizzes:
                calculated_exp += request.completed_quizzes * 50
            if request.average_score and request.completed_quizzes:
                score_bonus = int(request.average_score * request.completed_quizzes * 25)
                calculated_exp += score_bonus
            if request.total_lessons:
                calculated_exp += request.total_lessons * 10
        final_exp = calculated_exp
        if request.current_exp is not None or calculated_exp > 0:
            setattr(current_user, 'current_exp', final_exp)
        else:
            final_exp = getattr(current_user, 'current_exp', 0)
        level_changed = False
        if request.level is not None:
            setattr(current_user, 'level', request.level)
            setattr(current_user, 'require_exp', require_exp_for_level(request.level))
        else:
            current_level = getattr(current_user, 'level', 1)
            new_level, next_level_exp, level_increased = auto_level_up(final_exp, current_level)
            setattr(current_user, 'level', new_level)
            setattr(current_user, 'require_exp', next_level_exp)
            level_changed = level_increased
        if request.require_exp is not None:
            setattr(current_user, 'require_exp', request.require_exp)
        test_data: Dict[str, Any] = {}
        mapping = {
            'total_courses': 'test_total_courses',
            'completed_courses': 'test_completed_courses',
            'total_lessons': 'test_total_lessons',
            'total_quizzes': 'test_total_quizzes',
            'completed_quizzes': 'test_completed_quizzes',
            'average_score': 'test_average_score'
        }
        for field, key in mapping.items():
            value = getattr(request, field)
            if value is not None:
                test_data[key] = value
        if test_data:
            import json
            current_bio = getattr(current_user, 'bio', '') or ''
            if current_bio and not current_bio.endswith('\n'):
                current_bio += '\n'
            current_bio += f"[TEST_DATA] {json.dumps(test_data)}"
            setattr(current_user, 'bio', current_bio)
        db.commit()
        updated_stats = {
            "level": getattr(current_user, 'level'),
            "current_exp": getattr(current_user, 'current_exp'),
            "require_exp": getattr(current_user, 'require_exp'),
            "gained_exp": calculated_exp if request.current_exp is None else None,
            "calculated_exp_from_activities": calculated_exp if request.current_exp is None else None,
            "level_changed": level_changed,
            "original_stats": original_stats
        }
        rank_data = calculate_user_rank(current_user, db)
        updated_stats.update(rank_data)
        level_msg = ""
        if level_changed:
            level_msg = f" 🎉 LEVEL UP! {original_stats['level']} → {updated_stats['level']}"
        logger.info(f"Successfully updated test stats for user {current_user.email}: {updated_stats}")
        return TestStatsResponse(
            status=200,
            message=f"Cập nhật thành công! Level: {updated_stats['level']}, Exp: {updated_stats['current_exp']}, Rank: {updated_stats['rank']}{level_msg}",
            updated_stats=UpdatedStats(**updated_stats)
        )
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to update test stats for user {getattr(current_user, 'email', 'unknown')}: {e}")
        db.rollback()
        return TestStatsResponse(status=500, message="Có lỗi xảy ra khi cập nhật thống kê test")

async def reset_test_stats(current_user: User, db: Session) -> TestStatsResponse:
    try:
        setattr(current_user, 'level', 1)
        setattr(current_user, 'current_exp', 0)
        setattr(current_user, 'require_exp', require_exp_for_level(1))
        current_bio = getattr(current_user, 'bio', '') or ''
        lines = [l for l in current_bio.split('\n') if not l.startswith('[TEST_DATA]')]
        setattr(current_user, 'bio', '\n'.join(lines).strip())
        db.commit()
        rank_data = calculate_user_rank(current_user, db)
        reset_stats = {"level": 1, "current_exp": 0, "require_exp": require_exp_for_level(1), **rank_data}
        logger.info(f"Successfully reset test stats for user {current_user.email}")
        return TestStatsResponse(status=200, message="Đã reset thống kê về mặc định", updated_stats=UpdatedStats(**reset_stats))
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to reset test stats for user {getattr(current_user, 'email', 'unknown')}: {e}")
        db.rollback()
        return TestStatsResponse(status=500, message="Có lỗi xảy ra khi reset thống kê")

async def simulate_learning_activity(current_user: User, db: Session) -> TestStatsResponse:
    try:
        original_level = getattr(current_user, 'level', 1)
        original_exp = getattr(current_user, 'current_exp', 0)
        original_require_exp = getattr(current_user, 'require_exp', require_exp_for_level(original_level))
        activity_exp = 100 + 100 + 50  # Course + quizzes + bonus
        new_total_exp = original_exp + activity_exp
        setattr(current_user, 'current_exp', new_total_exp)
        new_level, next_level_exp, level_increased = auto_level_up(new_total_exp, original_level)
        setattr(current_user, 'level', new_level)
        setattr(current_user, 'require_exp', next_level_exp)
        db.commit()
        rank_data = calculate_user_rank(current_user, db)
        stats = {
            "original_level": original_level,
            "original_exp": original_exp,
            "original_require_exp": original_require_exp,
            "gained_exp": activity_exp,
            "activity_exp_gained": activity_exp,
            "new_level": new_level,
            "new_exp": new_total_exp,
            "new_require_exp": next_level_exp,
            "level_increased": level_increased,
            "levels_gained": new_level - original_level if level_increased else 0,
            **rank_data
        }
        level_msg = ""
        if level_increased:
            gained = new_level - original_level
            level_msg = f" 🎉 LEVEL UP! {original_level} → {new_level} (+{gained} level{'s' if gained > 1 else ''})"
        logger.info(f"Simulation completed for user {current_user.email}: {stats}")
        return TestStatsResponse(status=200, message=f"Mô phỏng hoạt động học tập! +{activity_exp} exp{level_msg}", updated_stats=UpdatedStats(**stats))
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to simulate activity for user {getattr(current_user, 'email', 'unknown')}: {e}")
        db.rollback()
        return TestStatsResponse(status=500, message="Có lỗi xảy ra khi mô phỏng hoạt động học tập")

async def add_experience(request, current_user: User, db: Session) -> TestStatsResponse:
    try:
        exp_amount = request.exp if hasattr(request, 'exp') else request
        logger.info("add_experience called: user=%s exp=%s", getattr(current_user, 'email', getattr(current_user, 'id', 'unknown')), exp_amount)
        original_level = getattr(current_user, 'level', 1)
        original_exp = getattr(current_user, 'current_exp', 0)
        original_require_exp = getattr(current_user, 'require_exp', require_exp_for_level(original_level))
        new_total_exp = original_exp + exp_amount
        setattr(current_user, 'current_exp', new_total_exp)
        new_level, next_level_exp, level_increased = auto_level_up(new_total_exp, original_level)
        setattr(current_user, 'level', new_level)
        setattr(current_user, 'require_exp', next_level_exp)
        db.commit()
        rank_data = calculate_user_rank(current_user, db)
        stats = {
            "original_level": original_level,
            "original_exp": original_exp,
            "original_require_exp": original_require_exp,
            "gained_exp": exp_amount,
            "new_level": new_level,
            "new_exp": new_total_exp,
            "new_require_exp": next_level_exp,
            "level_increased": level_increased,
            "levels_gained": new_level - original_level if level_increased else 0,
            "exp_progress_to_next": new_total_exp - get_exp_for_level(new_level),
            "exp_needed_for_next": next_level_exp - new_total_exp,
            **rank_data
        }
        level_msg = ""
        if level_increased:
            gained = new_level - original_level
            level_msg = f" 🎉 LEVEL UP! {original_level} → {new_level}" + (f" (+{gained} levels!)" if gained > 1 else "")
        logger.info("Experience added for user %s: %s", getattr(current_user, 'email', getattr(current_user, 'id', 'unknown')), stats)
        return TestStatsResponse(status=200, message=f"Thêm {exp_amount} exp thành công!{level_msg}", updated_stats=UpdatedStats(**stats))
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to add experience for user {getattr(current_user, 'email', 'unknown')}: {e}")
        db.rollback()
        return TestStatsResponse(status=500, message="Có lỗi xảy ra khi thêm kinh nghiệm", updated_stats=None)

async def get_level_system_info() -> dict:
    try:
        level_info = []
        for i, exp in enumerate(LEVEL_EXP_THRESHOLDS):
            level = i + 1
            next_exp = get_exp_for_level(level + 1)
            level_info.append({
                "level": level,
                "required_exp": exp,
                "next_level_exp": next_exp,
                "exp_to_next": next_exp - exp
            })
        for level in range(len(LEVEL_EXP_THRESHOLDS) + 1, len(LEVEL_EXP_THRESHOLDS) + 6):
            exp = get_exp_for_level(level)
            next_exp = get_exp_for_level(level + 1)
            level_info.append({
                "level": level,
                "required_exp": exp,
                "next_level_exp": next_exp,
                "exp_to_next": next_exp - exp,
                "calculated": True
            })
        return {
            "status": 200,
            "message": "Level system information",
            "level_system": {
                "max_predefined_level": len(LEVEL_EXP_THRESHOLDS),
                "growth_factor_beyond_max": 1.3,
                "levels": level_info
            }
        }
    except Exception as e:  # pragma: no cover
        logger.error(f"Error getting level system info: {e}")
        return {"status": 500, "message": "Có lỗi xảy ra khi lấy thông tin level system"}
