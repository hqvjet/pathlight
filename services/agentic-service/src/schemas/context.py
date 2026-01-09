from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class TestQA(BaseModel):
    question: str
    options: List[str]
    answer: int  # 1, 2, 3, or 4
    hint: str = ""
    explanation: str = ""
    difficulty: str = "medium"  # easy, medium, hard
    
    @field_validator('answer')
    @classmethod
    def validate_answer(cls, v):
        if not isinstance(v, int) or not (1 <= v <= 4):
            raise ValueError(f'answer must be int between 1-4, got {v}')
        return v
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        if not isinstance(v, list) or len(v) != 4:
            raise ValueError(f'options must be list of 4 items, got {len(v) if isinstance(v, list) else "not list"}')
        return v

class Lesson(BaseModel):
    lesson_id: str
    title: str
    overview: str
    content: str
    duration: int  # in minutes
    # Assessments for the lesson
    assessments: Optional[List[TestQA]] = None
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        # Chỉ kiểm tra content không rỗng, không enforce min/max length
        if not v or len(v.strip()) < 50:
            raise ValueError(f'content must have meaningful text (at least 50 chars), got {len(v) if v else 0}')
        return v

class Roadmap(BaseModel):
    """Roadmap item - mỗi item là 1 cột mốc/module/lesson plan"""
    title: str = Field(..., description="Tên cột mốc/module")
    description: str = Field(..., description="Mô tả ngắn gọn nội dung")

# Quiz-specific models - MUST be defined before Analysis classes that use them
class QuizIdea(BaseModel):
    """Idea for a quiz question - created by Planner"""
    topic: str = Field(..., description="Main topic/concept for the question")
    description: str = Field(..., description="Brief description of what to test")
    difficulty: str = Field(..., description="Difficulty level: easy, medium, hard")

class QuizCard(BaseModel):
    """Complete quiz question - created by Questioner"""
    card_id: str
    question: str
    hint: str
    explanation: str
    difficulty: str  # easy, medium, hard
    option1: str
    option2: str
    option3: str
    option4: str
    answer: int  # 1, 2, 3, or 4
    
    @field_validator('answer')
    @classmethod
    def validate_answer(cls, v):
        if not isinstance(v, int) or not (1 <= v <= 4):
            raise ValueError(f'answer must be int between 1-4, got {v}')
        return v

# CoT Analysis schemas
class CourseAnalysis(BaseModel):
    """Chain-of-Thought analysis before generating roadmap"""
    main_topic: str = Field(..., description="The PRIMARY subject this document is about (what is being taught/explained)")
    key_concepts: List[str] = Field(..., description="List of 3-5 main concepts covered in the document")
    implementation_tools: List[str] = Field(..., description="Tools/technologies mentioned (e.g., Python, Flask) - these are NOT the main topic")
    target_audience: str = Field(..., description="Who should learn this content")
    course_name: str = Field(..., description="Proposed course name based on the main_topic (100% Vietnamese)")
    course_description: str = Field(..., description="Brief course description (100% Vietnamese)")
    course_roadmap: List[Roadmap] = Field(..., description="Detailed roadmap covering the key_concepts (NOT implementation_tools)")

class LessonAnalysis(BaseModel):
    """Minimal CoT for lesson - just key reasoning before generating"""
    lesson_topic: str = Field(..., description="The specific topic this lesson covers")
    key_points: List[str] = Field(..., description="2-3 main points to cover")
    lesson_title: str = Field(..., description="Final lesson title (100% Vietnamese)")
    lesson_content: str = Field(..., description="Full lesson content in Markdown (100% Vietnamese)")

class QuizPlanAnalysis(BaseModel):
    """Minimal CoT for quiz plan - identify testable concepts"""
    main_topics: List[str] = Field(..., description="2-3 main topics from document")
    quiz_title: str = Field(..., description="Quiz title (100% Vietnamese)")
    quiz_overview: str = Field(..., description="Quiz overview (100% Vietnamese)")
    quiz_ideas: List[QuizIdea] = Field(..., description="Question ideas")

class QuestionAnalysis(BaseModel):
    """Minimal CoT for single question - think before creating"""
    concept: str = Field(..., description="The specific concept being tested")
    quiz_card: QuizCard = Field(..., description="The complete quiz question")

class State(BaseModel):
    id: str
    difficulty: str
    duration: int
    title: Optional[str] = None
    description: Optional[str] = None
    roadmap: Optional[List[Roadmap]] = None
    lessons: Optional[List[Lesson]] = None
    user_id: Optional[str] = None
    s3_bucket: Optional[str] = None
    # Iterative lesson creation progress
    lessons_expected: Optional[int] = None
    next_lesson_index: Optional[int] = None


class StateResponse(BaseModel):
    id: str
    difficulty: str
    duration: int
    title: Optional[str] = None
    description: Optional[str] = None
    roadmap: Optional[List[Roadmap]] = None
    lessons: Optional[List[Lesson]] = None


class QuizState(BaseModel):
    """State for quiz generation workflow"""
    id: str  # quiz_id
    difficulty: str
    duration: int
    num_questions: int  # Target number of questions
    user_id: Optional[str] = None
    
    # Generated by Planner
    title: Optional[str] = None
    overview: Optional[str] = None
    ideas: Optional[List[QuizIdea]] = None  # Question ideas from Planner
    retrieved_context: Optional[str] = None  # Retrieved context from planner (reused by questioner)
    
    # Generated by Questioner
    quiz_cards: Optional[List[QuizCard]] = None
    
    # Progress tracking
    ideas_expected: Optional[int] = None  # Should match num_questions
    next_card_index: Optional[int] = None  # For sequential generation


class QuizStateResponse(BaseModel):
    """Response schema for quiz generation"""
    id: str
    difficulty: str
    duration: int
    num_questions: int
    title: Optional[str] = None
    overview: Optional[str] = None
    ideas: Optional[List[QuizIdea]] = None
    quiz_cards: Optional[List[QuizCard]] = None