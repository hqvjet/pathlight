import os
import uuid
from typing import List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.logging import setup_logger
from .database import get_db, create_all, init_engine
from . import models as m
from schemas.context import State, Lesson, TestQA

logger = setup_logger(__name__)


def init_database() -> None:
    """Initialize engine and create tables if missing."""
    try:
        init_engine()
        create_all()
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)


def _difficulty_to_understand_level_id(difficulty: str) -> str:
    mapping = {
        "easy": "1",
        "medium": "2",
        "hard": "3",
    }
    return mapping.get(str(difficulty).lower(), "2")


def _ensure_understand_level(db: Session, difficulty: str) -> str:
    level_id = _difficulty_to_understand_level_id(difficulty)
    level = db.get(m.UnderstandLevelTag, level_id)
    if not level:
        level = m.UnderstandLevelTag(
            understand_level_id=level_id, understand_level=difficulty.capitalize()
        )
        db.add(level)
    return level_id


def _ensure_difficult_levels(db: Session) -> None:
    existing = {dl.difficult_level_id for dl in db.query(m.DifficultLevel).all()}
    defaults = [
        ("1", "easy"),
        ("2", "medium"),
        ("3", "hard"),
    ]
    for did, name in defaults:
        if did not in existing:
            db.add(m.DifficultLevel(difficult_level_id=did, difficult_level=name))


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def save_course_state(state: State) -> None:
    """Persist generated course State to Postgres.

    This function is idempotent by course_id: it will upsert CourseInfo and Course
    by their ids from state.id; lessons and tests are inserted based on the provided
    content. If rows already exist, it skips creating duplicates based on primary keys.
    """
    # If DATABASE_URL is not set, don't fail the main pipeline
    if not (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("PG_DSN")):
        logger.warning("DATABASE_URL not set; skipping DB persistence for course %s", state.id)
        return

    create_all()

    user_id = getattr(state, "user_id", None) or os.getenv("DEFAULT_USER_ID", "system")

    with next(get_db()) as db:  # type: ignore[misc]
        try:
            # Ensure runtime schema compatibility for older databases
            _ensure_runtime_schema(db)

            # Ensure reference tags
            _ensure_difficult_levels(db)
            understand_level_id = _ensure_understand_level(db, state.difficulty)

            # Upsert CourseInfo
            course_info_id = f"ci-{state.id}"
            ci = db.get(m.CourseInfo, course_info_id)
            if not ci:
                ci = m.CourseInfo(
                    course_info_id=course_info_id,
                    understand_level_id=understand_level_id,
                    title=state.title or "",
                    description=state.description or "",
                    duration=int(state.duration),
                    roadmap=("; ".join([r.title for r in state.roadmap or []])),
                )
                db.add(ci)
            else:
                ci.title = state.title or ci.title
                ci.description = state.description or ci.description
                ci.duration = int(state.duration)

            # Upsert Course
            course_id = state.id
            course = db.get(m.Course, course_id)
            if not course:
                course = m.Course(
                    course_id=course_id,
                    course_info_id=course_info_id,
                    user_id=user_id,
                    finish=False,
                )
                db.add(course)
            else:
                course.course_info_id = course_info_id

            # Lessons
            for idx, l in enumerate(state.lessons or [], start=1):
                lesson_id = l.lesson_id or f"{state.id}-L{idx}"
                exists = db.get(m.Lesson, lesson_id)
                if not exists:
                    exists = m.Lesson(
                        lesson_id=lesson_id,
                        course_id=course_id,
                        title=l.lesson_name or f"Lesson {idx}",
                        content=l.lesson_content or "",
                        description=l.lesson_description or "",
                        img_url=None,
                        finish=False,
                    )
                    db.add(exists)
                # Tests per lesson
                if l.tests:
                    test_id = f"t-{lesson_id}"
                    test = db.get(m.Test, test_id)
                    if not test:
                        test = m.Test(
                            test_id=test_id,
                            lesson_id=lesson_id,
                            title=f"Quiz for {exists.title}",
                            description="Auto-generated",
                            duration=10,
                            finish=False,
                            exp=10,
                        )
                        db.add(test)

                    # Clear existing QAs for idempotency (simple approach)
                    db.query(m.LessonQA).filter(m.LessonQA.test_id == test_id).delete()

                    for q in l.tests:
                        _insert_lesson_qa(db, test.test_id, q)

            # Final test
            if state.final_test:
                ft_id = f"ft-{course_id}"
                ft = db.get(m.FinalTest, ft_id)
                if not ft:
                    ft = m.FinalTest(
                        final_test_id=ft_id,
                        course_id=course_id,
                        title=f"Final Test for {state.title or course_id}",
                        description="Auto-generated",
                        duration=max(15, int(state.duration // 10)),
                        exp=50,
                    )
                    db.add(ft)

                # Reset QAs
                db.query(m.FinalQA).filter(m.FinalQA.final_test_id == ft_id).delete()
                for q in state.final_test:
                    _insert_final_qa(db, ft.final_test_id, q)

            db.commit()
            logger.info("Persisted course %s with %d lessons", state.id, len(state.lessons or []))
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception("DB error persisting course %s: %s", state.id, e)
        except Exception as e:
            db.rollback()
            logger.exception("Unexpected error persisting course %s: %s", state.id, e)


def _ensure_runtime_schema(db: Session) -> None:
    """Best-effort schema alignment for deployments missing new columns.

    - Adds final_qa.answer and final_qa.explanation if they don't exist.
    This is a safe, idempotent operation on Postgres.
    """
    try:
        db.execute(text("ALTER TABLE final_qa ADD COLUMN IF NOT EXISTS answer VARCHAR NOT NULL DEFAULT ''"))
        db.execute(text("ALTER TABLE final_qa ADD COLUMN IF NOT EXISTS explanation VARCHAR NOT NULL DEFAULT ''"))
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.warning("Schema ensure failed or not needed: %s", e)


def _insert_lesson_qa(db: Session, test_id: str, qa: TestQA) -> None:
    opts: List[str] = list(qa.options or [])
    while len(opts) < 4:
        opts.append("")
    item = m.LessonQA(
        qa_id=_gen_id("qa"),
        test_id=test_id,
        difficult_level_id=_difficulty_to_understand_level_id("medium"),
        question=qa.question,
        option1=opts[0],
        option2=opts[1],
        option3=opts[2],
        option4=opts[3],
    answer=qa.answer,
    explanation=getattr(qa, "explaination", None) or getattr(qa, "explanation", ""),
    )
    db.add(item)


def _insert_final_qa(db: Session, final_test_id: str, qa: TestQA) -> None:
    opts: List[str] = list(qa.options or [])
    while len(opts) < 4:
        opts.append("")
    item = m.FinalQA(
        final_qa_id=_gen_id("fqa"),
        final_test_id=final_test_id,
        question=qa.question,
        option1=opts[0],
        option2=opts[1],
        option3=opts[2],
        option4=opts[3],
    answer=qa.answer,
    explanation=getattr(qa, "explaination", None) or getattr(qa, "explanation", ""),
    )
    db.add(item)
