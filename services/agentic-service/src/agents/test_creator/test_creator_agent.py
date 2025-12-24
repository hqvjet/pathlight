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
        self.llm = llm_manager.get_llm(
            model_name=foundation_model, tools=list(self.tools.values())
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
            history.append(
                SystemMessage(
                    content=(
                        "Dừng gọi công cụ ngay. Hãy xuất JSON cuối cùng với trường assessments theo schema, không thêm giải thích."
                    )
                )
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

        # Parse response, accept map keyed by lesson_id or a direct list under assessments
        try:
            json_content = json.loads(ai.content)
        except Exception as e:
            tracer.record("error", "failed to parse ai json", lesson_id=lesson.lesson_id, error=str(e), content=str(ai.content)[:500])
            # FALLBACK: Try to force JSON response
            history.append(
                SystemMessage(
                    content=(
                        'CRITICAL: Trả về JSON với format:\n{"assessments": {"' + lesson.lesson_id + '": [...]}}.\n'
                        'Chỉ JSON, không text khác.'
                    )
                )
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
            try:
                json_content = json.loads(ai.content)
            except Exception:
                tracer.record("error", "fallback also failed", lesson_id=lesson.lesson_id)
                return

        # Try both old format (tests) and new format (assessments)
        # Format: {"tests": {"lesson_id": [{question, options, answer, ...}]}}
        assessments_payload = json_content.get("assessments") or json_content.get("tests")
        arr: Optional[List] = None
        
        if assessments_payload is None:
            tracer.record("error", "no assessments/tests field in response", lesson_id=lesson.lesson_id, keys=list(json_content.keys()))
            # FALLBACK 2: Force explicit JSON request
            history.append(
                SystemMessage(
                    content=(
                        'Response thiếu field "assessments". Hãy trả về lại với format:\n'
                        '{"assessments": {"' + lesson.lesson_id + '": [{...}]}}'
                    )
                )
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
            try:
                json_content = json.loads(ai.content)
                assessments_payload = json_content.get("assessments") or json_content.get("tests")
                if assessments_payload is None:
                    tracer.record("error", "fallback 2 failed - giving up", lesson_id=lesson.lesson_id)
                    return
            except Exception:
                tracer.record("error", "fallback 2 parse failed", lesson_id=lesson.lesson_id)
                return
            
        if isinstance(assessments_payload, dict):
            # Try exact match first
            arr = assessments_payload.get(lesson.lesson_id)
            # If not found, might be the only lesson
            if not arr and len(assessments_payload) == 1:
                arr = list(assessments_payload.values())[0]
        elif isinstance(assessments_payload, list):
            arr = assessments_payload

        if arr and isinstance(arr, list):
            # Coerce items to TestQA model shape with proper validation
            coerced: List[TestQA] = []
            for item in arr:
                try:
                    if isinstance(item, dict):
                        # Answer từ LLM là string (text của option đúng), convert sang index 1-4
                        answer_raw = item.get("answer")
                        options = item.get("options", [])
                        
                        if isinstance(answer_raw, str) and options:
                            # Tìm index của answer trong options (1-based)
                            try:
                                answer = options.index(answer_raw) + 1
                            except ValueError:
                                # Fallback: try to find partial match
                                answer = 1
                                for i, opt in enumerate(options):
                                    if answer_raw.strip().lower() in opt.strip().lower():
                                        answer = i + 1
                                        break
                        elif isinstance(answer_raw, int):
                            answer = answer_raw
                        else:
                            answer = 1
                        
                        if not (1 <= answer <= 4):
                            answer = 1
                        
                        coerced.append(TestQA(
                            question=item.get("question", ""),
                            options=item.get("options", [])[:4],
                            answer=answer,
                            hint=item.get("hint", ""),
                            explanation=item.get("explanation", "") or item.get("explaination", ""),
                            difficulty=item.get("difficulty", "medium")
                        ))
                except Exception as e:
                    tracer.record("warn", "failed to parse single assessment", error=str(e))
                    continue
            
            lesson.assessments = coerced
            tracer.record("done", "assessments attached", lesson_id=lesson.lesson_id, count=len(coerced))
        else:
            tracer.record("warn", "no assessments returned for lesson", lesson_id=lesson.lesson_id)
