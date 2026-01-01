from dotenv import load_dotenv
load_dotenv()

from typing import List, Optional
import json
import os
from agents.base.base_agent import BaseAgent
from agents.base.prompt_manager import PromptManager
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

from schemas.context import State, TestQA
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
from core.logging import setup_logger
from core.tracing import StepTracer
from core import status_tracker as status
from constant import MAX_TOOL_CALLS_PER_AGENT

# Token optimization: Keep only recent messages
MAX_HISTORY_MESSAGES = 10

def trim_history(history: List, max_messages: int = MAX_HISTORY_MESSAGES) -> List:
    """Keep only recent messages to prevent token explosion."""
    if len(history) <= max_messages:
        return history
    
    # Always keep system message (first)
    system_msg = history[0] if history and isinstance(history[0], SystemMessage) else None
    recent = history[-max_messages:]
    
    if system_msg and recent[0] != system_msg:
        return [system_msg] + recent
    return recent


class TestCreatorAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        foundation_model: str,
        prompt_manager: PromptManager,
        llm_manager: LLMManager,
        tool_manager: ToolManager,
    ):
        super().__init__(name, foundation_model, prompt_manager)
        self.tool_manager = tool_manager
        self.tools = {t.name: t for t in tool_manager.get_tools(name)}
        # CRITICAL FIX: Test creator needs moderate tokens for 4-6 assessments
        # Each assessment ~ 150-200 tokens, 6 assessments ~ 1200 tokens
        from constant import LLM_MAX_TOKENS_TEST
        self.llm = llm_manager.get_llm(
            model_name=foundation_model, 
            tools=list(self.tools.values()),
            max_tokens=LLM_MAX_TOKENS_TEST,
            enable_json_mode=True  # CRITICAL: Enable JSON mode
        )
        self.chain = self.build_chain(self.llm)
        self.logger = setup_logger(__name__)

    def __call__(self, state: State) -> State:
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        tracer.record("start", "invoke test creator", lessons=len(state.lessons or []))
        if not state.lessons:
            tracer.record("skip", "no lessons found in state")
            return state

        # Pick lessons that still need assessments
        target_lessons = [l for l in state.lessons if not getattr(l, "assessments", None)]
        if not target_lessons:
            tracer.record("skip", "all lessons already have assessments")
            return state

        tracer.record("sequential", "generate assessments sequentially (LangChain not thread-safe)", targets=len(target_lessons))

        # Generate assessments sequentially - LangChain chain.invoke() is NOT thread-safe
        # ThreadPoolExecutor causes all generations to fail
        failures = 0
        for idx, lesson in enumerate(target_lessons, 1):
            try:
                self._generate_single_lesson_tests(state, lesson)
                tracer.record("progress", f"assessment {idx}/{len(target_lessons)} completed", lesson_id=lesson.lesson_id)
            except Exception as e:
                failures += 1
                import traceback
                error_detail = traceback.format_exc()
                tracer.record("error", "test generation failed", lesson_id=lesson.lesson_id, error=str(e), traceback=error_detail[:500])
                self.logger.error(f"Test generation failed for {lesson.lesson_id}: {error_detail}")
                # Continue to next lesson instead of stopping

        tracer.record("done", "tests generation completed", failures=failures)
        try:
            # If all lessons have assessments now, mark lessons_ready
            if all(getattr(l, "assessments", None) for l in state.lessons or []):
                status.mark_lessons_ready(state.id, len(state.lessons or []))
        except Exception:
            pass
        return state

    def _generate_single_lesson_tests(self, state: State, lesson) -> None:
        """Generate tests for a single lesson, with tool-call cap and forced finalization."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)

        content = getattr(lesson, "content", None) or getattr(lesson, "lesson_content", None)
        if isinstance(content, str) and len(content) > 800:
            preview = content[:800] + "…"
        else:
            preview = content

        lessons_payload = [
            {
                "lesson_id": lesson.lesson_id,
                "title": getattr(lesson, "title", None) or getattr(lesson, "lesson_name", None),
                "overview": getattr(lesson, "overview", None) or getattr(lesson, "lesson_description", None),
                "content": preview,
            }
        ]

        history: List = [
            SystemMessage(
                content=self.prompt_manager.get_prompt(self.name).format(
                    id=state.id,
                    history=[],
                    difficulty=state.difficulty,
                    duration=str(state.duration),
                    lessons=lessons_payload,
                )
            )
        ]

        ai: AIMessage = self.chain.invoke(
            {
                "id": state.id,
                "history": history,
                "difficulty": state.difficulty,
                "duration": str(state.duration),
                "lessons": lessons_payload,
            }
        )
        tracer.record("llm", "initial response", lesson_id=lesson.lesson_id, content_preview=str(ai.content)[:200])

        count = 1
        while getattr(ai, "tool_calls", None) and count <= MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("tools", "llm requested tools", lesson_id=lesson.lesson_id, tool_calls=ai.tool_calls, iteration=count)
            for tool_call in ai.tool_calls:
                tool_name = tool_call["name"]
                tool_call_id = tool_call["id"]
                args = tool_call["args"]
                if tool_name not in self.tools:
                    raise ValueError(f"Tool {tool_name} not found in tools.")

                result = self.tool_manager.execute_tool_sync(tool_name, args)
                history.append(
                    ToolMessage(tool_call_id=tool_call_id, name=tool_name, content=result)
                )
                # Token optimization: Trim history to prevent explosion
                history = trim_history(history)
                tracer.record(
                    "tool_result",
                    f"{tool_name} executed",
                    lesson_id=lesson.lesson_id,
                    args=args,
                    result_preview=str(result)[:200],
                )

                ai = self.chain.invoke(
                    {
                        "id": state.id,
                        "history": history,
                        "difficulty": state.difficulty,
                        "duration": str(state.duration),
                        "lessons": lessons_payload,
                    }
                )
            count += 1

        if getattr(ai, "tool_calls", None):
            tracer.record(
                "warn",
                "tool budget exhausted; forcing final JSON output",
                lesson_id=lesson.lesson_id,
                rounds=count - 1,
                max_rounds=MAX_TOOL_CALLS_PER_AGENT,
            )
            self.logger.warning(f"Test Creator hit max tool calls: {MAX_TOOL_CALLS_PER_AGENT}")
            # CRITICAL: Create LLM WITHOUT tools binding to prevent further tool calls
            from langchain_openai import ChatOpenAI
            from constant import LLM_MAX_TOKENS_TEST, LLM_REQUEST_TIMEOUT
            final_llm = ChatOpenAI(
                model_name=self.foundation_model,
                openai_api_key=self.llm.openai_api_key,
                temperature=0.3,
                request_timeout=LLM_REQUEST_TIMEOUT,
                max_tokens=LLM_MAX_TOKENS_TEST,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
            final_chain = self.build_chain(final_llm)
            
            ai = final_chain.invoke(
                {
                    "id": state.id,
                    "history": history,
                    "difficulty": state.difficulty,
                    "duration": str(state.duration),
                    "lessons": lessons_payload,
                }
            )

        # CRITICAL FIX: Validate content before parsing
        if not ai.content or not ai.content.strip():
            tracer.record("error", "empty content", lesson_id=lesson.lesson_id, has_tool_calls=bool(getattr(ai, 'tool_calls', None)))
            raise ValueError(
                f"Test Creator {lesson.lesson_id}: LLM returned empty content. "
                f"Has tool_calls: {bool(getattr(ai, 'tool_calls', None))}"
            )
        
        # Log content for debugging
        self.logger.debug(f"Test Creator {lesson.lesson_id} content: {ai.content[:1000]}")
        
        # Parse response, accept map keyed by lesson_id or a direct list under assessments
        try:
            json_content = json.loads(ai.content)
        except Exception as e:
            tracer.record("error", "failed to parse ai json", lesson_id=lesson.lesson_id, error=str(e), content=str(ai.content)[:500])
            self.logger.error(f"Test Creator {lesson.lesson_id} parse error. Content: {ai.content[:1000]}")
            raise ValueError(f"Test Creator: Failed to parse JSON for {lesson.lesson_id} - {str(e)}")

        # CRITICAL FIX: Strict validation
        assessments_payload = json_content.get("assessments")
        if not assessments_payload:
            tracer.record("error", "no assessments field", lesson_id=lesson.lesson_id, keys=list(json_content.keys()))
            raise ValueError(f"Test Creator: Response missing 'assessments' field for {lesson.lesson_id}")
            
        arr: Optional[List] = None
        if isinstance(assessments_payload, dict):
            # Try exact match first
            arr = assessments_payload.get(lesson.lesson_id)
            # If not found, might be the only lesson
            if not arr and len(assessments_payload) == 1:
                arr = list(assessments_payload.values())[0]
        elif isinstance(assessments_payload, list):
            arr = assessments_payload

        if not arr or not isinstance(arr, list) or len(arr) < 3:
            tracer.record("error", "invalid assessments array", lesson_id=lesson.lesson_id, 
                         type=type(arr), count=len(arr) if isinstance(arr, list) else 0)
            raise ValueError(f"Test Creator: Need at least 3 assessments for {lesson.lesson_id}, got {len(arr) if isinstance(arr, list) else 0}")

        # CRITICAL FIX: Strict parsing with validation
        coerced: List[TestQA] = []
        for idx, item in enumerate(arr):
            try:
                if not isinstance(item, dict):
                    tracer.record("warn", f"assessment {idx} not dict", type=type(item))
                    continue
                
                # CRITICAL FIX: answer MUST be int 1-4
                answer_raw = item.get("answer")
                if not isinstance(answer_raw, int):
                    tracer.record("error", f"assessment {idx}: answer not int", 
                                 value=answer_raw, type=type(answer_raw))
                    continue
                
                if not (1 <= answer_raw <= 4):
                    tracer.record("error", f"assessment {idx}: answer out of range", value=answer_raw)
                    continue
                
                # Validate options
                options = item.get("options", [])
                if not isinstance(options, list) or len(options) != 4:
                    tracer.record("error", f"assessment {idx}: invalid options", 
                                 count=len(options) if isinstance(options, list) else "not list")
                    continue
                
                # Validate question
                question = item.get("question", "")
                if not question or len(question.strip()) < 10:
                    tracer.record("warn", f"assessment {idx}: question too short")
                    continue
                
                coerced.append(TestQA(
                    question=question,
                    options=options,
                    answer=answer_raw,
                    hint=item.get("hint", ""),
                    explanation=item.get("explanation", ""),
                    difficulty=item.get("difficulty", "medium")
                ))
            except Exception as e:
                tracer.record("warn", f"assessment {idx}: parse error", error=str(e))
                continue
        
        if len(coerced) < 3:
            tracer.record("error", "too few valid assessments after parsing", 
                         lesson_id=lesson.lesson_id, valid=len(coerced))
            raise ValueError(f"Test Creator: Only {len(coerced)} valid assessments for {lesson.lesson_id}, need at least 3")
        
        lesson.assessments = coerced
        tracer.record("done", "assessments attached", lesson_id=lesson.lesson_id, count=len(coerced))
