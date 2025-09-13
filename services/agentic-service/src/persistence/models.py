from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


class Course(Base):
    __tablename__ = "course"

    course_id = Column(String, primary_key=True)
    course_info_id = Column(String, ForeignKey("course_info.course_info_id"), nullable=False)
    user_id = Column(String, nullable=False)
    finish = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    course_info = relationship("CourseInfo", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course")


class CourseInfo(Base):
    __tablename__ = "course_info"

    course_info_id = Column(String, primary_key=True)
    understand_level_id = Column(String, ForeignKey("understand_level_tag.understand_level_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    roadmap = Column(String, nullable=True)

    courses = relationship("Course", back_populates="course_info")
    understand_level = relationship("UnderstandLevelTag", back_populates="course_infos")


class UnderstandLevelTag(Base):
    __tablename__ = "understand_level_tag"

    understand_level_id = Column(String, primary_key=True)
    understand_level = Column(String, nullable=False)

    course_infos = relationship("CourseInfo", back_populates="understand_level")


class Lesson(Base):
    __tablename__ = "lesson"

    lesson_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    description = Column(String, nullable=False)
    img_url = Column(String, nullable=True)
    finish = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    course = relationship("Course", back_populates="lessons")
    tests = relationship("Test", back_populates="lesson")


class Test(Base):
    __tablename__ = "test"

    test_id = Column(String, primary_key=True)
    lesson_id = Column(String, ForeignKey("lesson.lesson_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    finish = Column(Boolean, nullable=False, default=False)
    exp = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lesson = relationship("Lesson", back_populates="tests")
    lesson_qas = relationship("LessonQA", back_populates="test")


class LessonQA(Base):
    __tablename__ = "lesson_qa"

    qa_id = Column(String, primary_key=True)
    test_id = Column(String, ForeignKey("test.test_id"), nullable=False)
    difficult_level_id = Column(String, ForeignKey("difficult_level.difficult_level_id"), nullable=False)
    question = Column(String, nullable=False)
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    explanation = Column(String, nullable=False)

    test = relationship("Test", back_populates="lesson_qas")
    difficult_level = relationship("DifficultLevel", back_populates="lesson_qas")


class DifficultLevel(Base):
    __tablename__ = "difficult_level"

    difficult_level_id = Column(String, primary_key=True)
    difficult_level = Column(String, nullable=False)

    lesson_qas = relationship("LessonQA", back_populates="difficult_level")


class FinalTest(Base):
    __tablename__ = "final_test"

    final_test_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("course.course_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    exp = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", backref="final_tests")
    final_qas = relationship("FinalQA", back_populates="final_test")


class FinalQA(Base):
    __tablename__ = "final_qa"

    final_qa_id = Column(String, primary_key=True)
    final_test_id = Column(String, ForeignKey("final_test.final_test_id"), nullable=False)
    question = Column(String, nullable=False)
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    explanation = Column(String, nullable=False)

    final_test = relationship("FinalTest", back_populates="final_qas")
