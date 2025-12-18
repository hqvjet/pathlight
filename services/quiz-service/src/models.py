from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base


class Quiz(Base):
    __tablename__ = "quiz"

    quiz_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    publish = Column(Boolean, nullable=False, default=False, server_default=func.false())
    finish = Column(Boolean, nullable=False, default=False, server_default=func.false())
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    level = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    num_questions = Column(Integer, nullable=False)
    previous_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    cards = relationship("QuizCard", back_populates="quiz", cascade="all, delete-orphan")


class QuizCard(Base):
    __tablename__ = "quiz_card"

    card_id = Column(String, primary_key=True)
    quiz_id = Column(String, ForeignKey("quiz.quiz_id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(String, nullable=False)
    hint = Column(String, nullable=True)
    explanation = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    answer = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    quiz = relationship("Quiz", back_populates="cards")
