"""Generation status tracker backed by DynamoDB.

Provides real-time progress tracking for course generation workflow.
Frontend can poll this to show detailed progress to users.

REDESIGNED Schema for Better UI Tracking:

{
    "course_id": "xxx",  # PK
    "user_id": "xxx",
    
    # Overall status: "processing" | "done" | "error"
    "overall_status": "processing",
    "error_message": "",  # If overall_status = "error"
    
    # Step 1: Vectorization
    "vectorization_status": "done" | "processing" | "error",
    "vectorization_chunks": 46,
    "vectorization_error": "",
    
    # Step 2: Planning  
    "planning_status": "done" | "processing" | "error",
    "planning_course_title": "Hệ thống học tập tự định hướng Pathlight",
    "planning_roadmap_count": 6,
    "planning_error": "",
    
    # Step 3: Lessons
    "lessons_status": "processing" | "done" | "error",
    "lessons_completed": 2,
    "lessons_total": 6,
    "lessons_list": [
        {"id": "L1", "title": "Giới thiệu về Pathlight"},
        {"id": "L2", "title": "RAG Module"}
    ],
    "lessons_error": "",
    
    # Step 4: Tests/Assessments
    "tests_status": "processing" | "done" | "error",
    "tests_completed": 0,
    "tests_total": 6,
    "tests_error": "",
    
    # Timestamps
    "start_timestamp": 1234567890,
    "last_updated": 1234567890,
    "end_timestamp": 0,  # Set when overall_status = "done" or "error"
}

Usage:
- status_tracker.start(course_id, user_id)
- status_tracker.update_vectorization(course_id, status="done", chunks=46)
- status_tracker.update_planning(course_id, status="done", title="...", roadmap_count=6)
- status_tracker.update_lessons(course_id, status="processing", completed=2, total=6, lessons=[...])
- status_tracker.update_tests(course_id, status="done", completed=6, total=6)
- status_tracker.mark_error(course_id, step="lessons", error="...")
- status_tracker.mark_completed(course_id)
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
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


# ============================================================================
# NEW SCHEMA FUNCTIONS - Redesigned for Better UI Tracking
# ============================================================================

def start(course_id: str, user_id: str, strict: bool = True) -> None:
    """Initialize course generation tracking with new schema."""
    if not user_id or not str(user_id).strip():
        raise ValueError("user_id is required for status tracking")
    
    now = int(time.time())
    updates = {
        "user_id": str(user_id),
        "overall_status": "processing",
        "error_message": "",
        
        # Vectorization (Step 1)
        "vectorization_status": "processing",
        "vectorization_chunks": 0,
        "vectorization_error": "",
        
        # Planning (Step 2)  
        "planning_status": "processing",
        "planning_course_title": "",
        "planning_roadmap_count": 0,
        "planning_error": "",
        
        # Lessons (Step 3)
        "lessons_status": "processing",
        "lessons_completed": 0,
        "lessons_total": 0,
        "lessons_list": [],
        "lessons_error": "",
        
        # Tests (Step 4)
        "tests_status": "processing",
        "tests_completed": 0,
        "tests_total": 0,
        "tests_error": "",
        
        # Timestamps
        "start_timestamp": now,
        "last_updated": now,
        "end_timestamp": 0,
    }
    
    if strict:
        ensure_table(strict=True)
        update_item_strict(course_id, updates)
    else:
        update_item(course_id, updates)


def update_vectorization(course_id: str, status: str, chunks: int = 0, error: str = "") -> None:
    """Update vectorization step status.
    
    Args:
        status: "processing" | "done" | "error"
        chunks: Number of chunks indexed
        error: Error message if status="error"
    """
    update_item(course_id, {
        "vectorization_status": status,
        "vectorization_chunks": chunks,
        "vectorization_error": error,
        "last_updated": int(time.time()),
    })


def update_planning(course_id: str, status: str, title: str = "", roadmap_count: int = 0, error: str = "") -> None:
    """Update planning step status.
    
    Args:
        status: "processing" | "done" | "error"
        title: Course title
        roadmap_count: Number of roadmap items
        error: Error message if status="error"
    """
    update_item(course_id, {
        "planning_status": status,
        "planning_course_title": title,
        "planning_roadmap_count": roadmap_count,
        "planning_error": error,
        "last_updated": int(time.time()),
    })


def update_lessons(
    course_id: str, 
    status: str, 
    completed: int = 0, 
    total: int = 0, 
    lessons: Optional[List[Dict[str, str]]] = None,
    error: str = ""
) -> None:
    """Update lessons step status.
    
    Args:
        status: "processing" | "done" | "error"
        completed: Number of lessons completed
        total: Total lessons expected
        lessons: List of {"id": "L1", "title": "..."}
        error: Error message if status="error"
    """
    updates = {
        "lessons_status": status,
        "lessons_completed": completed,
        "lessons_total": total,
        "lessons_error": error,
        "last_updated": int(time.time()),
    }
    
    if lessons is not None:
        updates["lessons_list"] = lessons
    
    update_item(course_id, updates)


def update_tests(course_id: str, status: str, completed: int = 0, total: int = 0, error: str = "") -> None:
    """Update tests step status.
    
    Args:
        status: "processing" | "done" | "error"
        completed: Number of lessons with tests completed
        total: Total lessons needing tests
        error: Error message if status="error"
    """
    update_item(course_id, {
        "tests_status": status,
        "tests_completed": completed,
        "tests_total": total,
        "tests_error": error,
        "last_updated": int(time.time()),
    })


def mark_error(course_id: str, step: str, error: str) -> None:
    """Mark a specific step as error and set overall status to error.
    
    Args:
        step: "vectorization" | "planning" | "lessons" | "tests"
        error: Error message
    """
    now = int(time.time())
    updates = {
        "overall_status": "error",
        "error_message": error,
        "last_updated": now,
        "end_timestamp": now,
    }
    
    # Update specific step status
    if step == "vectorization":
        updates["vectorization_status"] = "error"
        updates["vectorization_error"] = error
    elif step == "planning":
        updates["planning_status"] = "error"
        updates["planning_error"] = error
    elif step == "lessons":
        updates["lessons_status"] = "error"
        updates["lessons_error"] = error
    elif step == "tests":
        updates["tests_status"] = "error"
        updates["tests_error"] = error
    
    update_item(course_id, updates)


def mark_completed(course_id: str) -> None:
    """Mark overall course generation as completed successfully."""
    now = int(time.time())
    update_item(course_id, {
        "overall_status": "done",
        "last_updated": now,
        "end_timestamp": now,
    })


# ============================================================================
# LEGACY FUNCTIONS - Kept for backward compatibility
# ============================================================================

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


def _estimate_time_remaining(status: str, lessons_have: int, lessons_total: int, start_time: Optional[float] = None) -> Optional[int]:
    """Estimate remaining time in seconds based on current progress."""
    if status == "completed" or status == "failed":
        return 0
    
    remaining = 0
    
    if status == "initializing":
        remaining = 30 + (lessons_total * 45) + 20 + 10
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


# Legacy - kept for compatibility
def mark_planning(course_id: str) -> None:
    """Legacy: Mark that planning phase has started."""
    update_planning(course_id, status="processing")


def mark_plan_ready(course_id: str, title: Optional[str], description: Optional[str], roadmap_count: int) -> None:
    """Legacy: Mark that course plan is ready."""
    update_planning(course_id, status="done", title=title or "", roadmap_count=roadmap_count)
    update_lessons(course_id, status="processing", total=roadmap_count)


def mark_lessons_progress(course_id: str, have: int, planned: int) -> None:
    """Legacy: Update lesson creation progress."""
    update_lessons(course_id, status="processing", completed=have, total=planned)


def mark_lessons_ready(course_id: str, count: int) -> None:
    """Legacy: Mark that all lessons are created."""
    update_lessons(course_id, status="done", completed=count, total=count)
    update_tests(course_id, status="processing", total=count)


def mark_tests_ready(course_id: str) -> None:
    """Legacy: Mark that tests/assessments are ready."""
    # Read current item to get tests_total, then mark done with completed=total
    from infrastructure.aws.dynamo_client import _resource, _ensure_table, _table_name
    resource = _resource()
    table_name = _table_name()
    table = _ensure_table(resource, table_name) if resource else None
    
    tests_total = 0
    if table:
        try:
            resp = table.get_item(Key={"course_id": course_id})
            item = resp.get("Item", {})
            tests_total = item.get("tests_total", 0)
        except Exception:
            pass
    
    # Mark as done with completed = total
    update_tests(course_id, status="done", completed=tests_total, total=tests_total)


def mark_failed(course_id: str, error_message: str) -> None:
    """Legacy: Mark course generation as failed with error message."""
    mark_error(course_id, step="", error=error_message)


def mark_final_ready(course_id: str, count: int) -> None:
    """Legacy: marks final tests ready."""
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
