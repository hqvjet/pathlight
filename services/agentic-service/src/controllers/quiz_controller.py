from typing import Dict
from factories.quiz_agent_factory import invoke_quiz_agent
from schemas.context import QuizState
from core.logging import setup_logger
from core.exceptions import InternalServerError
from core import status_tracker as status
from persistence import save_quiz_state, init_database


class QuizController:
    def __init__(self):
        self.logger = setup_logger(__name__)

    def generate_quiz(self, quiz_id: str, difficulty: str, duration: int, num_questions: int, user_id: str) -> QuizState:
        """Generate a quiz using the multi-agent system.
        
        Args:
            quiz_id: Unique quiz identifier (also used for retrieval from OpenSearch)
            difficulty: Difficulty level (easy, medium, hard)
            duration: Target duration in seconds
            num_questions: Number of questions to generate
            user_id: Owner user ID
            
        Returns:
            QuizState with generated quiz data
        """
        # Validate user_id is present
        if not user_id:
            raise InternalServerError("user_id is required to generate a quiz")
        
        # Build initial state
        init_state = QuizState(
            id=quiz_id,
            difficulty=difficulty,
            duration=duration,
            num_questions=num_questions,
            user_id=user_id,
        )

        try:
            self.logger.info("Invoking quiz agent for quiz_id=%s", quiz_id)
            result = invoke_quiz_agent(init_state)
        except ValueError as e:
            # Validation errors
            self.logger.error(f"Quiz generation validation error: {str(e)}")
            try:
                status.mark_quiz_failed(quiz_id, f"Validation error: {str(e)}")
            except Exception:
                pass
            raise InternalServerError(f"Quiz generation validation failed: {str(e)}")
        except Exception as e:
            # Catch-all errors
            import traceback
            error_trace = traceback.format_exc()
            self.logger.error(f"Quiz generation failed with error: {error_trace}")
            try:
                status.mark_quiz_failed(quiz_id, f"Error: {str(e)}")
            except Exception:
                pass
            raise InternalServerError(f"Quiz generation failed: {str(e)}")

        # Log summary
        try:
            quiz_cards = getattr(result, "quiz_cards", []) or []
            self.logger.info(
                "generate_quiz finished | title=%s | ideas=%s | cards=%s",
                getattr(result, "title", None),
                len(getattr(result, "ideas", []) or []),
                len(quiz_cards),
            )
        except Exception:
            pass

        # Persist to database
        try:
            init_database()
            # Ensure user_id survives
            if isinstance(result, QuizState):
                if not result.user_id and user_id:
                    result.user_id = user_id
                save_quiz_state(result)
            else:
                if not result.get("user_id") and user_id:
                    result["user_id"] = user_id
                save_quiz_state(QuizState(**result))  # type: ignore[arg-type]
        except ValueError as e:
            raise InternalServerError(str(e))
        except Exception:
            self.logger.exception("Quiz persistence failed for %s", quiz_id)

        # Return result
        if isinstance(result, QuizState):
            return result
        try:
            return QuizState(**result)  # type: ignore[arg-type]
        except Exception:
            raise InternalServerError("Agent returned unexpected result shape")
