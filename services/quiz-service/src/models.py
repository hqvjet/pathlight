from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base


class QuizInfo(Base):
    __tablename__ = "quiz_info"
    
    quiz_info_id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)
    play_time = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quizzes = relationship("Quiz", back_populates="quiz_info")


class Quiz(Base):
    __tablename__ = "quiz"
    
    quiz_id = Column(String, primary_key=True)
    quiz_info_id = Column(String, ForeignKey("quiz_info.quiz_info_id"), nullable=False)
    user_id = Column(String, nullable=False)  # Foreign key to user service
    finish = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quiz_info = relationship("QuizInfo", back_populates="quizzes")
    quiz_qas = relationship("QuizQA", back_populates="quiz")


class QuizQA(Base):
    __tablename__ = "quiz_qa"
    
    qa_id = Column(String, primary_key=True)
    quiz_id = Column(String, ForeignKey("quiz.quiz_id"), nullable=False)
    question = Column(Text, nullable=True)
    explain = Column(Text, nullable=True)
    option1 = Column(String, nullable=True)
    option2 = Column(String, nullable=True)
    option3 = Column(String, nullable=True)
    option4 = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quiz = relationship("Quiz", back_populates="quiz_qas")
