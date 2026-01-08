import os
import uuid
from typing import List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.logging import setup_logger
from .database import get_db, create_all, init_engine
from . import models as m
from schemas.context import QuizState, QuizCard

logger = setup_logger(__name__)


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def save_quiz_state(state: QuizState) -> None:
    """Persist generated quiz State to Postgres.
    
    Schema:
    - quiz: quiz_id, user_id (FK to users), publish, finish, title, overview, level, duration, num_questions
    - quiz_card: card_id, quiz_id, question, hint, explanation, difficulty, option1-4, answer (int)
    """
    # Validate user_id exists
    if not state.user_id:
        logger.error("Cannot save quiz %s: user_id is required", state.id)
        raise ValueError(f"user_id is required to save quiz {state.id}")
    
    # If DATABASE_URL is not set, skip
    if not (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("PG_DSN")):
        logger.warning("DATABASE_URL not set; skipping DB persistence for quiz %s", state.id)
        return

    create_all()

    with next(get_db()) as db:  # type: ignore[misc]
        try:
            # Upsert Quiz
            quiz_id = state.id
            quiz = db.get(m.Quiz, quiz_id)
            if not quiz:
                quiz = m.Quiz(
                    quiz_id=quiz_id,
                    user_id=state.user_id,
                    publish=False,
                    finish=False,
                    title=state.title or "Untitled Quiz",
                    overview=state.overview or "",
                    level=state.difficulty,
                    duration=int(state.duration),
                    num_questions=state.num_questions,
                    previous_score=None,
                )
                db.add(quiz)
            else:
                # Update existing quiz
                quiz.title = state.title or quiz.title
                quiz.overview = state.overview or quiz.overview
                quiz.level = state.difficulty
                quiz.duration = int(state.duration)
                quiz.num_questions = state.num_questions

            # Quiz Cards
            quiz_cards = state.quiz_cards or []
            
            # Clear existing cards (idempotent)
            db.query(m.QuizCard).filter(m.QuizCard.quiz_id == quiz_id).delete()
            
            for card in quiz_cards:
                _insert_quiz_card(db, quiz_id, card)

            db.commit()
            logger.info("Persisted quiz %s with %d cards", state.id, len(quiz_cards))
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception("DB error persisting quiz %s: %s", state.id, e)
        except Exception as e:
            db.rollback()
            logger.exception("Unexpected error persisting quiz %s: %s", state.id, e)


def _insert_quiz_card(db: Session, quiz_id: str, card: QuizCard) -> None:
    """Insert quiz card (question) for a quiz."""
    # Ensure answer is int 1-4
    answer_int = card.answer if isinstance(card.answer, int) else 1
    if not (1 <= answer_int <= 4):
        answer_int = 1
    
    item = m.QuizCard(
        card_id=card.card_id,
        quiz_id=quiz_id,
        question=card.question,
        hint=card.hint or "",
        explanation=card.explanation or "",
        difficulty=card.difficulty or "medium",
        option1=card.option1,
        option2=card.option2,
        option3=card.option3,
        option4=card.option4,
        answer=answer_int,
    )
    db.add(item)
