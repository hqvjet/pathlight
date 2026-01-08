from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


class Course(Base):
    __tablename__ = "course"

    course_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)  # FK to users.user_id (owner)
    publish = Column(Boolean, nullable=False, default=False)
    finish = Column(Boolean, nullable=False, default=False)
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    level = Column(String, nullable=False)  # easy, medium, hard
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lesson"

    lesson_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id"), nullable=False)
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    content = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    course = relationship("Course", back_populates="lessons")
    assessments = relationship("Assessment", back_populates="lesson", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessment"

    assessment_id = Column(String, primary_key=True)
    lesson_id = Column(String, ForeignKey("lesson.lesson_id"), nullable=False)
    question = Column(String, nullable=False)
    hint = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # easy, medium, hard
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    answer = Column(Integer, nullable=False)  # 1, 2, 3, or 4
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lesson = relationship("Lesson", back_populates="assessments")


class Quiz(Base):
    __tablename__ = "quiz"

    quiz_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)  # FK to users.user_id (owner)
    publish = Column(Boolean, nullable=False, default=False)
    finish = Column(Boolean, nullable=False, default=False)
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    level = Column(String, nullable=False)  # easy, medium, hard
    duration = Column(Integer, nullable=False)
    num_questions = Column(Integer, nullable=False)
    previous_score = Column(Integer, nullable=True)  # Optional: for retake tracking
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    quiz_cards = relationship("QuizCard", back_populates="quiz", cascade="all, delete-orphan")


class QuizCard(Base):
    __tablename__ = "quiz_card"

    card_id = Column(String, primary_key=True)
    quiz_id = Column(String, ForeignKey("quiz.quiz_id"), nullable=False)
    question = Column(String, nullable=False)
    hint = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # easy, medium, hard
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    answer = Column(Integer, nullable=False)  # 1, 2, 3, or 4
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    quiz = relationship("Quiz", back_populates="quiz_cards")
