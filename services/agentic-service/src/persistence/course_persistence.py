import os
import uuid
from typing import List

from sqlalchemy.exc import SQLAlchemyError
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


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def save_course_state(state: State) -> None:
    """Persist generated course State to Postgres theo ERD.
    
    Schema:
    - course: course_id, user_id (FK to users), publish, finish, title, overview, level, duration
    - lesson: lesson_id, course_id, title, overview, content, duration
    - assessment: assessment_id, lesson_id, question, hint, explanation, difficulty, option1-4, answer (int)
    """
    # Validate user_id exists (required by DB constraint)
    if not state.user_id:
        logger.error("Cannot save course %s: user_id is required", state.id)
        raise ValueError(f"user_id is required to save course {state.id}")
    
    # If DATABASE_URL is not set, don't fail the main pipeline
    if not (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("PG_DSN")):
        logger.warning("DATABASE_URL not set; skipping DB persistence for course %s", state.id)
        return

    create_all()

    with next(get_db()) as db:  # type: ignore[misc]
        try:
            # Upsert Course
            course_id = state.id
            course = db.get(m.Course, course_id)
            if not course:
                course = m.Course(
                    course_id=course_id,
                    user_id=state.user_id,  # Required: owner user id
                    publish=False,
                    finish=False,
                    title=state.title or "Untitled Course",
                    overview=state.description or "",
                    level=state.difficulty,
                    duration=int(state.duration),
                )
                db.add(course)
            else:
                # Update existing course
                course.title = state.title or course.title
                course.overview = state.description or course.overview
                course.level = state.difficulty
                course.duration = int(state.duration)
                # user_id should not change after creation

            # Lessons
            for idx, lesson in enumerate(state.lessons or [], start=1):
                lesson_id = lesson.lesson_id or f"{state.id}-L{idx}"
                
                existing_lesson = db.get(m.Lesson, lesson_id)
                if not existing_lesson:
                    existing_lesson = m.Lesson(
                        lesson_id=lesson_id,
                        course_id=course_id,
                        title=lesson.title or f"Lesson {idx}",
                        overview=lesson.overview or "",
                        content=lesson.content or "",
                        duration=lesson.duration or 30,
                    )
                    db.add(existing_lesson)
                else:
                    # Update existing
                    existing_lesson.title = lesson.title or existing_lesson.title
                    existing_lesson.overview = lesson.overview or existing_lesson.overview
                    existing_lesson.content = lesson.content or existing_lesson.content
                    existing_lesson.duration = lesson.duration or existing_lesson.duration

                # Assessments for this lesson
                if lesson.assessments:
                    # Clear existing assessments (idempotent)
                    db.query(m.Assessment).filter(m.Assessment.lesson_id == lesson_id).delete()
                    
                    for qa in lesson.assessments:
                        _insert_assessment(db, lesson_id, qa)

            db.commit()
            logger.info("Persisted course %s with %d lessons", state.id, len(state.lessons or []))
            
            # Index course vector for recommendation system
            try:
                from services.recommendation_service import RecommendationService
                rec_service = RecommendationService()
                rec_service.index_course_vector(
                    course_id=state.id,
                    title=state.title or "Untitled Course",
                    description=state.description or "",
                    user_id=state.user_id,
                    publish=False,  # Default to unpublished
                    level=state.difficulty,
                    duration=int(state.duration)
                )
            except Exception as e:
                logger.warning(f"Failed to index course vector for recommendations: {e}")
                
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception("DB error persisting course %s: %s", state.id, e)
        except Exception as e:
            db.rollback()
            logger.exception("Unexpected error persisting course %s: %s", state.id, e)


def _insert_assessment(db: Session, lesson_id: str, qa: TestQA) -> None:
    """Insert assessment (quiz question) for a lesson."""
    opts: List[str] = list(qa.options or [])
    while len(opts) < 4:
        opts.append("")
    
    # Ensure answer is int 1-4
    answer_int = qa.answer if isinstance(qa.answer, int) else 1
    if not (1 <= answer_int <= 4):
        answer_int = 1
    
    item = m.Assessment(
        assessment_id=_gen_id("asmt"),
        lesson_id=lesson_id,
        question=qa.question,
        hint=getattr(qa, "hint", "") or "",
        explanation=getattr(qa, "explanation", "") or "",
        difficulty=getattr(qa, "difficulty", "medium") or "medium",
        option1=opts[0],
        option2=opts[1],
        option3=opts[2],
        option4=opts[3],
        answer=answer_int,
    )
    db.add(item)


def get_lesson_content(lesson_id: str) -> dict:
    """Retrieve lesson content from database.
    
    Args:
        lesson_id: Lesson identifier
        
    Returns:
        Dictionary with lesson details or empty dict if not found
    """
    # If DATABASE_URL is not set, return empty
    if not (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("PG_DSN")):
        logger.warning("DATABASE_URL not set; cannot retrieve lesson %s", lesson_id)
        return {}
    
    try:
        init_database()
        with next(get_db()) as db:  # type: ignore[misc]
            lesson = db.get(m.Lesson, lesson_id)
            if not lesson:
                logger.warning("Lesson %s not found in database", lesson_id)
                return {}
            
            return {
                "lesson_id": lesson.lesson_id,
                "course_id": lesson.course_id,
                "title": lesson.title,
                "overview": lesson.overview,
                "content": lesson.content,
                "duration": lesson.duration,
            }
    except Exception as e:
        logger.exception("Failed to retrieve lesson %s: %s", lesson_id, e)
        return {}
