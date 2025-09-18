import asyncio
from typing import Any, Dict
from factories.agent_factory import invoke_course_agent
from schemas.agent_schemas import AgentRequest, AgentResponse
from schemas.context import State
from core.logging import setup_logger
from core.exceptions import InternalServerError
from persistence import save_course_state, init_database

class AgentController:
    def __init__(self):
        self.logger = setup_logger(__name__)

    async def generate_course(self, request: AgentRequest) -> State:
        # Build initial state for the agent graph
        init_state = State(
            id=request.id,
            difficulty=request.difficulty,
            duration=request.duration,
            user_id=request.user_id,
        )

        try:
            # 15-minute timeout guard
            result = await asyncio.wait_for(invoke_course_agent(init_state), timeout=900)
        except asyncio.TimeoutError:
            raise InternalServerError("Course generation timed out after 15 minutes")

        # concise summary instead of full payload to console
        try:
            lessons = getattr(result, "lessons", []) or []
            self.logger.info(
                "generate_course finished | title=%s | roadmap_len=%s | lessons=%s",
                getattr(result, "title", None),
                len(getattr(result, "roadmap", []) or []),
                len(lessons),
            )
        except Exception:
            pass

        # Persist to database (best effort; don't fail main flow if DB missing)
        try:
            init_database()
            # Ensure user_id survives through the agent pipeline
            if isinstance(result, State):
                if not getattr(result, "user_id", None) and request.user_id:
                    result.user_id = request.user_id
                save_course_state(result)
            else:
                if not result.get("user_id") and request.user_id:
                    result["user_id"] = request.user_id
                save_course_state(State(**result))  # type: ignore[arg-type]
        except Exception:
            self.logger.exception("Course persistence step failed for %s", request.id)

        # Ensure we return a Pydantic model or plain JSON serializable dict
        if isinstance(result, State):
            return result
        try:
            return State(**result)  # type: ignore[arg-type]
        except Exception:
            # Last resort
            raise InternalServerError("Agent returned unexpected result shape")
