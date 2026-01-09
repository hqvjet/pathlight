"""Generation status tracker backed by DynamoDB.

Provides real-time progress tracking for course generation workflow.
Frontend can poll this to show detailed progress to users.

Schema (DynamoDB Item):
- course_id (PK)
- user_id: string (owner)
- status: string (enum: "initializing", "planning", "creating_lessons", "creating_tests", "finalizing", "completed", "failed")
- progress_percentage: int (0-100)
- current_step: string (human-readable current step)
- current_step_detail: string (detailed info about current step)
- title_ready: bool
- lessons_ready: bool
- tests_ready: bool
- vectorized: bool (true when content is indexed in vector DB)
- final_ready: bool (true when entire course generation is completed)
- title: string
- description: string
- roadmap_count: int
- lessons_count: int
- lessons_planned: int
- estimated_time_remaining_seconds: int (optional)
- error_message: string (if failed)
- updated_at: iso8601 (auto)

Progress Flow:
1. initializing (0%) - Starting workflow
2. planning (20%) - Creating course plan & roadmap
3. creating_lessons (40-80%) - Generating lessons sequentially
4. creating_tests (85%) - Adding assessments (if needed)
5. finalizing (95%) - Final validation
6. completed (100%) - Done!

Usage:
- status_tracker.start(course_id, user_id)
- status_tracker.mark_planning()
- status_tracker.mark_plan_ready(course_id, title, desc, roadmap_count)
- status_tracker.mark_lessons_progress(course_id, have, planned)
- status_tracker.mark_lessons_ready(course_id, count)
- status_tracker.mark_tests_ready(course_id)
- status_tracker.mark_vectorized(course_id, ok=True)
- status_tracker.mark_completed(course_id)  # Sets final_ready=True
- status_tracker.mark_failed(course_id, error)
"""

from __future__ import annotations

from typing import Optional
import time

from infrastructure.aws.dynamo_client import (
    put_item,
    update_item,
    put_item_strict,
    ensure_table,
    update_item_strict,
)


def _calculate_progress_percentage(status: str, lessons_have: int = 0, lessons_total: int = 0) -> int:
    """Calculate progress percentage based on current status and lesson progress."""
    if status == "initializing":
        return 0
    elif status == "vectorizing":
        return 5
    elif status == "vectorized":
        return 10
    elif status == "planning":
        return 20
    elif status == "creating_lessons":
        if lessons_total > 0:
            # 40% to 80% range for lessons
            lesson_progress = (lessons_have / lessons_total) * 40
            return int(40 + lesson_progress)
        return 40
    elif status == "creating_tests":
        return 85
    elif status == "finalizing":
        return 95
    elif status == "completed":
        return 100
    elif status == "failed":
        return 0  # Reset on failure
    return 0


def _estimate_time_remaining(status: str, lessons_have: int, lessons_total: int, start_time: Optional[float] = None) -> Optional[int]:
    """Estimate remaining time in seconds based on current progress.
    
    Assumptions:
    - Planning: ~30 seconds
    - Each lesson: ~45 seconds
    - Tests: ~20 seconds
    - Finalizing: ~10 seconds
    """
    if status == "completed" or status == "failed":
        return 0
    
    remaining = 0
    
    if status == "initializing":
        remaining = 30 + (lessons_total * 45) + 20 + 10  # Everything ahead
    elif status == "planning":
        remaining = 30 + (lessons_total * 45) + 20 + 10
    elif status == "creating_lessons":
        lessons_left = lessons_total - lessons_have
        remaining = (lessons_left * 45) + 20 + 10
    elif status == "creating_tests":
        remaining = 20 + 10
    elif status == "finalizing":
        remaining = 10
    
    return remaining if remaining > 0 else None


def start(course_id: str, user_id: str, strict: bool = True) -> None:
    """Initialize course generation tracking.
    
    Sets status to 'initializing' with 0% progress.
    """
    if not user_id or not str(user_id).strip():
        raise ValueError("user_id is required for status tracking")
    
    updates = {
        "status": "initializing",
        "progress_percentage": 0,
        "current_step": "Khởi tạo",
        "current_step_detail": "Đang khởi tạo workflow tạo khóa học...",
        "user_id": str(user_id),
        "title_ready": False,
        "lessons_ready": False,
        "tests_ready": False,
        "vectorized": False,  # Add vectorized boolean field
        "final_ready": False,  # Add final_ready boolean field
        "start_timestamp": int(time.time()),
    }
    
    if strict:
        ensure_table(strict=True)
        update_item_strict(course_id, updates)
    else:
        update_item(course_id, updates)


def mark_planning(course_id: str) -> None:
    """Mark that planning phase has started."""
    update_item(
        course_id,
        {
            "status": "planning",
            "progress_percentage": 20,
            "current_step": "Lập kế hoạch",
            "current_step_detail": "Đang phân tích yêu cầu và tạo roadmap khóa học...",
        },
    )


def mark_plan_ready(course_id: str, title: Optional[str], description: Optional[str], roadmap_count: int) -> None:
    """Mark that course plan is ready.
    
    Updates status to indicate planning is complete and lesson creation is about to start.
    """
    update_item(
        course_id,
        {
            "status": "creating_lessons",
            "progress_percentage": 40,
            "current_step": "Tạo bài học",
            "current_step_detail": f"Đã hoàn thành roadmap với {roadmap_count} bài học. Bắt đầu tạo nội dung...",
            "title_ready": True,
            "title": title or "",
            "description": description or "",
            "roadmap_count": roadmap_count,
            "lessons_planned": roadmap_count,
        },
    )


def mark_lessons_progress(course_id: str, have: int, planned: int) -> None:
    """Update lesson creation progress.
    
    This is called after each lesson is created successfully.
    Progress: 40% (start) to 80% (all lessons done)
    """
    progress_pct = _calculate_progress_percentage("creating_lessons", have, planned)
    time_remaining = _estimate_time_remaining("creating_lessons", have, planned)
    
    updates = {
        "status": "creating_lessons",
        "progress_percentage": progress_pct,
        "current_step": f"Tạo bài học {have}/{planned}",
        "current_step_detail": f"Đang tạo nội dung chi tiết cho bài học thứ {have}...",
        "lessons_count": have,
        "lessons_planned": planned,
    }
    
    if time_remaining:
        updates["estimated_time_remaining_seconds"] = time_remaining
    
    update_item(course_id, updates)


def mark_lessons_ready(course_id: str, count: int) -> None:
    """Mark that all lessons are created.
    
    Moves to tests creation phase or finalizing.
    """
    update_item(
        course_id,
        {
            "status": "creating_tests",
            "progress_percentage": 85,
            "current_step": "Tạo bài kiểm tra",
            "current_step_detail": f"Đã hoàn thành {count} bài học. Đang tạo câu hỏi đánh giá...",
            "lessons_ready": True,
            "lessons_count": count,
        },
    )


def mark_tests_ready(course_id: str) -> None:
    """Mark that tests/assessments are ready."""
    update_item(
        course_id,
        {
            "status": "finalizing",
            "progress_percentage": 95,
            "current_step": "Hoàn thiện",
            "current_step_detail": "Đang hoàn thiện và lưu khóa học...",
            "tests_ready": True,
        },
    )


def mark_completed(course_id: str) -> None:
    """Mark course generation as completed successfully."""
    update_item(
        course_id,
        {
            "status": "completed",
            "progress_percentage": 100,
            "current_step": "Hoàn thành",
            "current_step_detail": "Khóa học đã được tạo thành công!",
            "estimated_time_remaining_seconds": 0,
            "final_ready": True,  # Add final_ready boolean field
            "end_timestamp": int(time.time()),
        },
    )


def mark_failed(course_id: str, error_message: str) -> None:
    """Mark course generation as failed with error message."""
    update_item(
        course_id,
        {
            "status": "failed",
            "progress_percentage": 0,
            "current_step": "Thất bại",
            "current_step_detail": "Đã xảy ra lỗi trong quá trình tạo khóa học",
            "error_message": error_message,
            "end_timestamp": int(time.time()),
        },
    )


def mark_final_ready(course_id: str, count: int) -> None:
    """Legacy compatibility - marks final tests ready."""
    mark_tests_ready(course_id)


def mark_vectorized(course_id: str, ok: bool = True) -> None:
    update_item_strict(course_id, {"vectorized": bool(ok)})


# Quiz generation tracking functions
QUIZ_TRACKING_TABLE = "quiz_generation_tracking"


def start_quiz(quiz_id: str, user_id: str, strict: bool = True) -> None:
    """Initialize quiz generation tracking.
    
    Sets status to 'initializing' with 0% progress.
    """
    if not user_id or not str(user_id).strip():
        raise ValueError("user_id is required for quiz tracking")
    
    updates = {
        "status": "initializing",
        "progress_percentage": 0,
        "current_step": "Khởi tạo",
        "current_step_detail": "Đang khởi tạo workflow tạo quiz...",
        "user_id": str(user_id),
        "plan_ready": False,
        "questions_ready": False,
        "vectorized": False,  # Track if quiz content is indexed in vector DB
        "final_ready": False,  # Track if entire quiz generation is completed
        "start_timestamp": int(time.time()),
    }
    
    if strict:
        ensure_table(strict=True, table_name=QUIZ_TRACKING_TABLE, pk_name="quiz_id")
        update_item_strict(quiz_id, updates, table_name=QUIZ_TRACKING_TABLE, pk_name="quiz_id")
    else:
        update_item(quiz_id, updates, table_name=QUIZ_TRACKING_TABLE, pk_name="quiz_id")


def mark_quiz_planning(quiz_id: str) -> None:
    """Mark that quiz planning phase has started."""
    update_item(
        quiz_id,
        {
            "status": "planning",
            "progress_percentage": 20,
            "current_step": "Lập kế hoạch",
            "current_step_detail": "Đang phân tích yêu cầu và tạo ý tưởng câu hỏi...",
        },
        table_name=QUIZ_TRACKING_TABLE,
        pk_name="quiz_id",
    )


def mark_quiz_plan_ready(quiz_id: str, title: str, overview: str, ideas_count: int) -> None:
    """Mark that quiz plan is ready."""
    update_item(
        quiz_id,
        {
            "status": "creating_questions",
            "progress_percentage": 40,
            "current_step": "Tạo câu hỏi",
            "current_step_detail": f"Đã hoàn thành {ideas_count} ý tưởng câu hỏi. Bắt đầu tạo nội dung...",
            "plan_ready": True,
            "title": title or "",
            "overview": overview or "",
            "ideas_count": ideas_count,
        },
        table_name=QUIZ_TRACKING_TABLE,
        pk_name="quiz_id",
    )


def mark_quiz_questions_progress(quiz_id: str, have: int, planned: int) -> None:
    """Update quiz question creation progress."""
    # 40% to 90% range for questions
    if planned > 0:
        question_progress = (have / planned) * 50
        progress_pct = int(40 + question_progress)
    else:
        progress_pct = 40
    
    update_item(
        quiz_id,
        {
            "status": "creating_questions",
            "progress_percentage": progress_pct,
            "current_step": f"Tạo câu hỏi {have}/{planned}",
            "current_step_detail": f"Đang tạo nội dung chi tiết cho câu hỏi thứ {have}...",
            "questions_count": have,
            "questions_planned": planned,
        },
        table_name=QUIZ_TRACKING_TABLE,
        pk_name="quiz_id",
    )


def mark_quiz_questions_ready(quiz_id: str, count: int) -> None:
    """Mark that all quiz questions are created."""
    update_item(
        quiz_id,
        {
            "status": "finalizing",
            "progress_percentage": 95,
            "current_step": "Hoàn thiện",
            "current_step_detail": f"Đã hoàn thành {count} câu hỏi. Đang hoàn thiện và lưu quiz...",
            "questions_ready": True,
            "questions_count": count,
        },
        table_name=QUIZ_TRACKING_TABLE,
        pk_name="quiz_id",
    )


def mark_quiz_completed(quiz_id: str) -> None:
    """Mark quiz generation as completed successfully."""
    update_item(
        quiz_id,
        {
            "status": "completed",
            "progress_percentage": 100,
            "current_step": "Hoàn thành",
            "current_step_detail": "Quiz đã được tạo thành công!",
            "final_ready": True,  # Set final_ready when quiz is fully completed
            "end_timestamp": int(time.time()),
        },
        table_name=QUIZ_TRACKING_TABLE,
        pk_name="quiz_id",
    )


def mark_quiz_failed(quiz_id: str, error_message: str) -> None:
    """Mark quiz generation as failed with error message."""
    update_item(
        quiz_id,
        {
            "status": "failed",
            "progress_percentage": 0,
            "current_step": "Thất bại",
            "current_step_detail": "Đã xảy ra lỗi trong quá trình tạo quiz",
            "error_message": error_message,
            "end_timestamp": int(time.time()),
        },
        table_name=QUIZ_TRACKING_TABLE,
        pk_name="quiz_id",
    )


def mark_quiz_vectorized(quiz_id: str, ok: bool = True) -> None:
    """Mark that quiz content has been indexed in vector DB."""
    update_item_strict(
        quiz_id, 
        {"vectorized": bool(ok)},
        table_name=QUIZ_TRACKING_TABLE,
        pk_name="quiz_id"
    )
