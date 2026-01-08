from schemas.context import QuizState
from core.logging import setup_logger
from core.tracing import StepTracer
from core import status_tracker as status


class QuizOrchestrator:
    def __init__(self):
        self.logger = setup_logger(__name__)

    def __call__(self, state: QuizState) -> str:
        tracer = StepTracer("quiz_orchestrator", state.id, logger=self.logger)
        tracer.record(
            "start",
            "route next step for quiz",
            title=state.title,
            ideas_count=len(state.ideas or []),
            quiz_cards=len(state.quiz_cards or []),
            expected=state.num_questions,
        )

        # Required fields
        id = state.id
        difficulty = state.difficulty
        duration = state.duration
        num_questions = state.num_questions

        # Generated/Progress
        title = state.title
        overview = state.overview
        ideas = state.ideas or []
        quiz_cards = state.quiz_cards or []

        if not id or not difficulty or not duration or not num_questions:
            raise ValueError("ID, Difficulty, Duration, and num_questions are required in the state.")

        # 1) Need a plan (title, overview, ideas)
        if not title or not overview or not ideas:
            tracer.record("decide", "quiz_planner needed (no title/overview/ideas)")
            # Start tracking
            try:
                if getattr(state, "user_id", None):
                    status.start_quiz(id, state.user_id)
            except Exception:
                pass
            return "create_quiz_plan"

        # 2) Generate quiz cards sequentially from ideas
        current_count = len(quiz_cards)
        if current_count < num_questions:
            tracer.record(
                "decide",
                "questioner needed (sequential)",
                current=current_count,
                expected=num_questions,
            )
            return "create_quiz_question"

        tracer.record("done", "quiz workflow complete")
        # Mark as completed
        try:
            if title or overview:
                status.mark_quiz_plan_ready(id, title, overview, len(ideas))
            if quiz_cards:
                status.mark_quiz_questions_ready(id, len(quiz_cards))
            status.mark_quiz_completed(id)
        except Exception:
            pass
        return "done"
