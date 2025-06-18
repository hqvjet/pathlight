from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base


class Course(Base):
    __tablename__ = "course"
    
    course_id = Column(String, primary_key=True)
    course_info_id = Column(String, ForeignKey("course_info.course_info_id"), nullable=False)
    user_id = Column(String, nullable=False)  # Foreign key to user service
    finish = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course_info = relationship("CourseInfo", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course")


class CourseInfo(Base):
    __tablename__ = "course_info"
    
    course_info_id = Column(String, primary_key=True)
    understand_level_id = Column(String, ForeignKey("understand_level_tag.understand_level_id"), nullable=False)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    courses = relationship("Course", back_populates="course_info")
    understand_level = relationship("UnderstandLevelTag", back_populates="course_infos")


class UnderstandLevelTag(Base):
    __tablename__ = "understand_level_tag"
    
    understand_level_id = Column(String, primary_key=True)
    understand_level = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course_infos = relationship("CourseInfo", back_populates="understand_level")


class Lesson(Base):
    __tablename__ = "lesson"
    
    lesson_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id"), nullable=False)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    img_url = Column(String, nullable=False)
    finish = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    tests = relationship("Test", back_populates="lesson")


class Test(Base):
    __tablename__ = "test"
    
    test_id = Column(String, primary_key=True)
    lesson_id = Column(String, ForeignKey("lesson.lesson_id"), nullable=False)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)
    finish = Column(Boolean, nullable=False, default=False)
    exp_int = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lesson = relationship("Lesson", back_populates="tests")
    lesson_qas = relationship("LessonQA", back_populates="test")


class LessonQA(Base):
    __tablename__ = "lesson_qa"
    
    qa_id = Column(String, primary_key=True)
    test_id = Column(String, ForeignKey("test.test_id"), nullable=False)
    difficult_level_id = Column(String, ForeignKey("difficult_level.difficult_level_id"), nullable=False)
    question = Column(Text, nullable=True)
    option1 = Column(String, nullable=True)
    option2 = Column(String, nullable=True)
    option3 = Column(String, nullable=True)
    option4 = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    test = relationship("Test", back_populates="lesson_qas")
    difficult_level = relationship("DifficultLevel", back_populates="lesson_qas")


class DifficultLevel(Base):
    __tablename__ = "difficult_level"
    
    difficult_level_id = Column(String, primary_key=True)
    difficult_level = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lesson_qas = relationship("LessonQA", back_populates="difficult_level")
