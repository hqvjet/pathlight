from typing import Any, Dict
from factories.agent_factory import invoke_course_agent
from schemas.agent_schemas import AgentRequest, AgentResponse
from schemas.context import State
from core.logging import setup_logger
from core.exceptions import InternalServerError
from core import status_tracker as status
from persistence import save_course_state, init_database

class AgentController:
    def __init__(self):
        self.logger = setup_logger(__name__)

    def generate_course(self, request: AgentRequest) -> State:
        # Validate user_id is present (required by DB)
        if not request.user_id:
            raise InternalServerError("user_id is required to generate a course")
        
        # Build initial state for the agent graph
        init_state = State(
            id=request.id,
            difficulty=request.difficulty,
            duration=request.duration,
            user_id=request.user_id,
        )

        try:
            self.logger.info("Invoking course agent with recursion_limit=%s", getattr(__import__('config').config, 'RECURSION_LIMIT', 500))
            result = invoke_course_agent(init_state)
        except ValueError as e:
            # Validation errors from agents (schema mismatch, missing fields, etc.)
            self.logger.error(f"Course generation validation error: {str(e)}")
            # Mark as failed in tracking
            try:
                status.mark_failed(request.id, f"Validation error: {str(e)}")
            except Exception:
                pass
            raise InternalServerError(f"Course generation validation failed: {str(e)}")
        except Exception as e:
            # Catch-all for other errors
            import traceback
            error_trace = traceback.format_exc()
            self.logger.error(f"Course generation failed with error: {error_trace}")
            # Mark as failed in tracking
            try:
                status.mark_failed(request.id, f"Error: {str(e)}")
            except Exception:
                pass
            raise InternalServerError(f"Course generation failed: {str(e)}")

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
                if not result.user_id and request.user_id:
                    result.user_id = request.user_id
                save_course_state(result)
            else:
                if not result.get("user_id") and request.user_id:
                    result["user_id"] = request.user_id
                save_course_state(State(**result))  # type: ignore[arg-type]
        except ValueError as e:
            # Re-raise validation errors (like missing user_id)
            raise InternalServerError(str(e))
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
