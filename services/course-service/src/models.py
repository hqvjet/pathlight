from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base


class Course(Base):
    __tablename__ = "course"

    course_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    publish = Column(Boolean, nullable=False, default=False, server_default=func.false())
    finish = Column(Boolean, nullable=False, default=False, server_default=func.false())
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    level = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    learning_progress = relationship("LearningProgress", back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lesson"

    lesson_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False)
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
    lesson_id = Column(String, ForeignKey("lesson.lesson_id", ondelete="CASCADE"), nullable=False)
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

    lesson = relationship("Lesson", back_populates="assessments")


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    user_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id", ondelete="CASCADE"), primary_key=True)
    num_finished_lesson = Column(Integer, nullable=False, default=0, server_default="0")
    num_total_lesson = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    course = relationship("Course", back_populates="learning_progress")
