from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base


class Course(Base):
    __tablename__ = "course"
    course_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    level = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False, server_default=func.false())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    progress_records = relationship("CourseProgress", back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lesson"
    lesson_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id"), nullable=False)
    title = Column(String, nullable=False)
    overview = Column(String, nullable=False)
    content = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    course = relationship("Course", back_populates="lessons")
    assessments = relationship("Assessment", back_populates="lesson", cascade="all, delete-orphan")
    progress_records = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")


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


class CourseProgress(Base):
    __tablename__ = "course_progress"

    progress_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    finish = Column(Boolean, nullable=False, default=False, server_default=func.false())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="progress_records")

    __table_args__ = (UniqueConstraint('user_id', 'course_id', name='uq_user_course_progress'),)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    progress_id = Column(String, primary_key=True)
    lesson_id = Column(String, ForeignKey("lesson.lesson_id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    finish = Column(Boolean, nullable=False, default=False, server_default=func.false())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    lesson = relationship("Lesson", back_populates="progress_records")

    __table_args__ = (UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson_progress'),)
