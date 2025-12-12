from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base


class Course(Base):
    __tablename__ = "course"
    course_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    finish = Column(Boolean, nullable=False, default=False)
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    level = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lesson"
    lesson_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id"), nullable=False)
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    content = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    finish = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    course = relationship("Course", back_populates="lessons")
    assessments = relationship("Assessment", back_populates="lesson", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessment"

    assessment_id = Column(String, primary_key=True)
    lesson_id = Column(String, ForeignKey("lesson.lesson_id"), nullable=False)
    question = Column(String, nullable=False)
    hint = Column(String, nullable=True)
    explanation = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    answer = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lesson = relationship("Lesson", back_populates="assessments")


class Quiz(Base):
    __tablename__ = "quiz"

    quiz_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id"), nullable=False)
    user_id = Column(String, nullable=False)
    finish = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    course = relationship("Course", back_populates="quizzes")
    quiz_qas = relationship("QuizQA", back_populates="quiz", cascade="all, delete-orphan")


class QuizQA(Base):
    __tablename__ = "quiz_qa"

    qa_id = Column(String, primary_key=True)
    quiz_id = Column(String, ForeignKey("quiz.quiz_id"), nullable=False)
    question = Column(String, nullable=False)
    explain = Column(String, nullable=False)
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    answer = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    quiz = relationship("Quiz", back_populates="quiz_qas")
