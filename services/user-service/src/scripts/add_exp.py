#!/usr/bin/env python3
"""
One-off script to add (or subtract) experience for a user by email or id.
Usage:
  python add_exp.py --email user@example.com --delta 30
  python add_exp.py --id <user-id> --delta -50

This script uses the same SQLAlchemy models/config as the user-service.
Make sure your environment variables (DATABASE_URL, etc.) match your runtime.
"""
import sys
import argparse
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[2]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from database import SessionLocal
from models import User
try:
    from services.experience_service import auto_level_up
except Exception:
    # If import fails, define a fallback auto_level_up that tries to approximate
    # level/next-requirement using get_exp_for_level if possible, otherwise
    # returns a conservative result. This avoids returning None for level.
    def auto_level_up(current_exp: int, current_level: int | None = None):
        if current_level is None:
            current_level = 1
        try:
            # Try to import helper to compute thresholds
            from services.experience_service import get_exp_for_level

            level = 1
            # Find highest level such that current_exp < next level threshold
            while True:
                next_req = get_exp_for_level(level + 1)
                if current_exp < next_req:
                    break
                level += 1
                if level > 10000:
                    break
            next_req = get_exp_for_level(level + 1)
            level_increased = current_level is not None and level > current_level
            return level, next_req, level_increased
        except Exception:
            # As a last resort, return current_level (or 1) and set next_req
            # to a sensible non-zero value derived from current_exp.
            return (current_level or 1), max(1, current_exp or 1), False


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email", help="User email to find the account")
    group.add_argument("--id", dest="user_id", help="User ID to find the account")
    parser.add_argument("--delta", type=int, required=True, help="Amount of exp to add (use negative for penalty)")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        if args.email:
            user = session.query(User).filter(User.email == args.email).first()
        else:
            user = session.query(User).filter(User.id == args.user_id).first()
        if not user:
            print("User not found")
            return 2

        profile = getattr(user, 'profile', None)
        if not profile:
            profile = user._ensure_profile()
            session.add(profile)
            session.flush()

        original_exp = int(getattr(profile, 'current_exp', 0) or 0)
        original_level = int(getattr(profile, 'level', 1) or 1)

        new_total = original_exp + args.delta
        if new_total < 0:
            new_total = 0

        # compute new level and next requirement
        try:
            new_level, next_req, _ = auto_level_up(new_total, original_level)
        except Exception:
            new_level = original_level
            next_req = getattr(profile, 'require_exp', 0) or 0

        setattr(profile, 'current_exp', new_total)
        setattr(profile, 'level', int(new_level))
        setattr(profile, 'require_exp', int(next_req))

        session.commit()
        print(f"Updated user: id={user.id} email={user.email}")
        print(f"exp: {original_exp} -> {new_total}, level: {original_level} -> {new_level}, require_exp={next_req}")
        return 0
    except Exception as e:
        session.rollback()
        print("Error:", e)
        return 3
    finally:
        session.close()


if __name__ == '__main__':
    raise SystemExit(main())
