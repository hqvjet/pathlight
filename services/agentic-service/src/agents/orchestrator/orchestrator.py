from schemas.context import State
from core.logging import setup_logger
from core.tracing import StepTracer
from core import status_tracker as status


class Orchestrator:
    def __init__(self):
        self.logger = setup_logger(__name__)

    def __call__(self, state: State) -> str:
        tracer = StepTracer("orchestrator", state.id, logger=self.logger)
        # Summarize the incoming state compactly
        tracer.record(
            "start",
            "route next step",
            title=state.title,
            roadmap_len=len(state.roadmap or []),
            lessons=len(state.lessons or []),
            expected=state.lessons_expected,
        )

        # Required
        id = state.id
        difficulty = state.difficulty
        duration = state.duration

        # Generated/Progress
        title = state.title
        description = state.description
        roadmap = state.roadmap or []
        lessons = state.lessons or []
        expected = state.lessons_expected

        if not id or not difficulty or not duration:
            raise ValueError("ID, Difficulty, Duration are required in the state.")

        # 1) Need a plan
        if not title and not description and not roadmap:
            tracer.record("decide", "planner needed (no title/description/roadmap)")
            # Start tracking in DynamoDB at the very beginning (requires user_id)
            try:
                if getattr(state, "user_id", None):
                    status.start(id, state.user_id)
            except Exception:
                pass
            return "create_plan"

        # 2) Generate lessons ONE BY ONE (sequential) to prevent timeout
        planned_total = expected or (len(roadmap) if roadmap else None)
        if planned_total:
            current_count = len(lessons)
            if current_count < planned_total:
                tracer.record(
                    "decide",
                    "lesson creator (sequential)",
                    current=current_count,
                    planned=planned_total,
                )
                try:
                    status.mark_lessons_progress(id, current_count, planned_total)
                except Exception:
                    pass
                return "create_lesson"
        else:
            # No planned total - fallback
            if len(lessons) == 0:
                tracer.record("decide", "lesson creator initial (no lessons yet)")
                try:
                    status.mark_plan_ready(id, title, description, len(roadmap))
                except Exception:
                    pass
                return "create_lesson"

        # 3) After lessons done, create tests if any lesson lacks tests
        for l in lessons:
            if not getattr(l, "assessments", None):
                tracer.record("decide", "test creator needed", lesson_id=l.lesson_id)
                return "create_test"

        tracer.record("done", "workflow complete")
        # Update final readiness statuses
        try:
            if title or description or roadmap:
                status.mark_plan_ready(id, title, description, len(roadmap))
            if lessons:
                status.mark_lessons_ready(id, len(lessons))
        except Exception:
            pass
        return "done"
