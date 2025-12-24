from dotenv import load_dotenv
load_dotenv()

from typing import List, Optional
import json
import os
import asyncio
from agents.base.base_agent import BaseAgent
from agents.base.prompt_manager import PromptManager
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

from schemas.context import State, Lesson
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
from core.logging import setup_logger
from core.tracing import StepTracer
from core import status_tracker as status
from constant import MAX_TOOL_CALLS_PER_AGENT
from agents.lesson_creator.parallel_helper import generate_lessons_parallel

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


class LessonCreatorAgent(BaseAgent):
    def __init__(
        self, name: str,
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
        tracer.record("start", "invoke lesson creator", difficulty=state.difficulty, duration=state.duration)

        lessons = state.lessons or []
        if state.lessons is None:
            state.lessons = lessons

        # Determine total planned lessons
        planned_total: Optional[int] = state.lessons_expected or (len(state.roadmap) if state.roadmap else None)

        # Generate ALL lessons in PARALLEL if none exist yet (FAST PATH - PARALLEL)
        if planned_total and len(lessons) == 0:
            tracer.record("parallel", "generate all lessons in parallel", count=planned_total)
            results = generate_lessons_parallel(self, state, planned_total)
            if results:
                lessons.extend(results)
                tracer.record("done", f"generated {len(results)} lessons in parallel", total=len(lessons))
            else:
                # Fallback: create placeholder lessons
                for i in range(1, planned_total + 1):
                    lid = f"{state.id}-L{i}"
                    lessons.append(Lesson(
                        lesson_id=lid,
                        title=f"Lesson {i}",
                        overview="",
                        content="",
                        duration=30
                    ))
                tracer.record("warn", "batch generation failed; placeholders used")
            
            state.next_lesson_index = len(lessons) + 1
            try:
                status.mark_lessons_progress(state.id, len(lessons), planned_total)
            except Exception:
                pass
            return state

        # Fallback: generate lessons one by one (SLOW PATH - only when partial)
        if planned_total and len(lessons) < planned_total:
            start_index = len(lessons) + 1
            tracer.record("single", "generate next lesson", index=start_index)
            prev_ids = [l.lesson_id for l in lessons]

            result = self._generate_single_lesson(state, start_index, prev_ids)
            if result is None:
                lid = f"{state.id}-L{start_index}"
                tracer.record("warn", "lesson generation returned None; placeholder used", index=start_index)
                lessons.append(Lesson(
                    lesson_id=lid,
                    title=f"Lesson {start_index}",
                    overview="",
                    content="",
                    duration=30
                ))
            else:
                lessons.append(result)

            state.next_lesson_index = start_index + 1
            tracer.record("done", "lesson appended", lesson_id=lessons[-1].lesson_id, next_index=state.next_lesson_index)
            try:
                status.mark_lessons_progress(state.id, len(lessons), planned_total)
            except Exception:
                pass
            return state

        # Fallback when total is unknown
        next_index = state.next_lesson_index or (len(lessons) + 1)
        result = self._generate_single_lesson(state, next_index, [l.lesson_id for l in lessons])
        if result is None:
            lid = f"{state.id}-L{next_index}"
            lessons.append(Lesson(
                lesson_id=lid,
                title=f"Lesson {next_index}",
                overview="",
                content="",
                duration=30
            ))
        else:
            lessons.append(result)
        state.next_lesson_index = next_index + 1
        tracer.record("done", "single lesson appended", lesson_id=lessons[-1].lesson_id, next_index=state.next_lesson_index)
        try:
            planned = planned_total or len(state.roadmap or []) if 'planned_total' in locals() else len(state.roadmap or [])
            status.mark_lessons_progress(state.id, len(lessons), planned)
        except Exception:
            pass
        return state

    def _generate_all_lessons(self, state: State, count: int) -> Optional[List[Lesson]]:
        """Generate ALL lessons at once for speed (batch mode)."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        
        history: List = [
            SystemMessage(
                content=self.prompt_manager.get_prompt(self.name).format(
                    id=state.id,
                    history=[],
                    difficulty=state.difficulty,
                    duration=str(state.duration),
                    title=state.title,
                    description=state.description,
                    roadmap=state.roadmap,
                    lessons_expected=count,
                    next_lesson_index="all",  # Signal to generate all
                    prev_lessons=[],
                )
            )
        ]

        ai: AIMessage = self.chain.invoke(
            {
                "id": state.id,
                "history": history,
                "difficulty": state.difficulty,
                "duration": str(state.duration),
                "title": state.title,
                "description": state.description,
                "roadmap": state.roadmap,
                "lessons_expected": count,
                "next_lesson_index": "all",
                "prev_lessons": [],
            }
        )
        tracer.record("llm", "batch initial response", content_preview=str(ai.content)[:200])

        iteration = 1
        while getattr(ai, "tool_calls", None) and iteration <= MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("tools", "batch llm requested tools", tool_calls=ai.tool_calls, iteration=iteration)
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
                history = trim_history(history)
                tracer.record(
                    "tool_result",
                    f"{tool_name} executed",
                    args=args,
                    result_preview=str(result)[:200],
                )

                ai = self.chain.invoke(
                    {
                        "id": state.id,
                        "history": history,
                        "difficulty": state.difficulty,
                        "duration": str(state.duration),
                        "title": state.title,
                        "description": state.description,
                        "roadmap": state.roadmap,
                        "lessons_expected": count,
                        "next_lesson_index": "all",
                        "prev_lessons": [],
                    }
                )
            iteration += 1

        if getattr(ai, "tool_calls", None):
            tracer.record("warn", "batch tool budget exhausted", rounds=iteration - 1)
            history.append(
                SystemMessage(
                    content="Ngừng gọi công cụ. Xuất JSON cuối cùng với tất cả lessons theo schema."
                )
            )
            ai = self.chain.invoke(
                {
                    "id": state.id,
                    "history": history,
                    "difficulty": state.difficulty,
                    "duration": str(state.duration),
                    "title": state.title,
                    "description": state.description,
                    "roadmap": state.roadmap,
                    "lessons_expected": count,
                    "next_lesson_index": "all",
                    "prev_lessons": [],
                }
            )

        # Parse all lessons from response
        try:
            json_content = json.loads(ai.content)
        except Exception as e:
            tracer.record("error", "batch failed to parse json", error=str(e))
            return None

        lessons_data = json_content.get("lessons") or []
        if not isinstance(lessons_data, list):
            lessons_data = [lessons_data] if lessons_data else []
        
        if not lessons_data:
            tracer.record("warn", "batch no lessons in response")
            return None

        # Parse each lesson
        lessons = []
        for idx, obj in enumerate(lessons_data, 1):
            lesson_id = obj.get("lesson_id") or f"{state.id}-L{idx}"
            title = obj.get("title") or obj.get("lesson_name") or f"Lesson {idx}"
            overview = obj.get("overview") or obj.get("lesson_description") or ""
            content = obj.get("content") or obj.get("lesson_content") or ""
            duration = obj.get("duration") or 30
            
            # Parse assessments if present
            assessments_raw = obj.get("assessments") or []
            assessments = []
            for qa in assessments_raw:
                try:
                    answer = qa.get("answer")
                    if isinstance(answer, str):
                        import re
                        match = re.search(r'\d+', str(answer))
                        answer = int(match.group()) if match else 1
                    elif not isinstance(answer, int):
                        answer = 1
                    
                    if not (1 <= answer <= 4):
                        answer = 1
                    
                    assessments.append({
                        "question": qa.get("question", ""),
                        "options": qa.get("options", []),
                        "answer": answer,
                        "hint": qa.get("hint", ""),
                        "explanation": qa.get("explanation", ""),
                        "difficulty": qa.get("difficulty", "medium")
                    })
                except Exception as e:
                    tracer.record("warn", f"lesson {idx}: failed to parse assessment", error=str(e))
                    continue
            
            lesson = Lesson(
                lesson_id=lesson_id,
                title=title,
                overview=overview,
                content=content,
                duration=duration,
                assessments=assessments if assessments else None
            )
            lessons.append(lesson)

        tracer.record("done", "batch generated", count=len(lessons))
        return lessons

    def _generate_single_lesson(self, state: State, index: int, prev_lessons: List[str]) -> Optional[Lesson]:
        """Generate one lesson for the given index, with tool-call loop and robust JSON parsing."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)

        # Keep roadmap minimal: only the current item to reduce tokens
        slim_roadmap = None
        if state.roadmap and len(state.roadmap) >= index:
            try:
                slim_roadmap = [state.roadmap[index - 1]]
            except Exception:
                slim_roadmap = state.roadmap[:1]

        history: List = [
            SystemMessage(
                content=self.prompt_manager.get_prompt(self.name).format(
                    id=state.id,
                    history=[],
                    difficulty=state.difficulty,
                    duration=str(state.duration),
                    title=state.title,
                    description=state.description,
                    roadmap=slim_roadmap or state.roadmap,
                    lessons_expected=state.lessons_expected or "",
                    next_lesson_index=str(index),
                    prev_lessons=prev_lessons,
                )
            )
        ]

        ai: AIMessage = self.chain.invoke(
            {
                "id": state.id,
                "history": history,
                "difficulty": state.difficulty,
                "duration": str(state.duration),
                "title": state.title,
                "description": state.description,
                "roadmap": slim_roadmap or state.roadmap,
                "lessons_expected": state.lessons_expected or "",
                "next_lesson_index": str(index),
                "prev_lessons": prev_lessons,
            }
        )
        tracer.record("llm", "initial response", index=index, content_preview=str(ai.content)[:200])

        count = 1
        while getattr(ai, "tool_calls", None) and count <= MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("tools", "llm requested tools", index=index, tool_calls=ai.tool_calls, iteration=count)
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
                    index=index,
                    args=args,
                    result_preview=str(result)[:200],
                )

                ai = self.chain.invoke(
                    {
                        "id": state.id,
                        "history": history,
                        "difficulty": state.difficulty,
                        "duration": str(state.duration),
                        "title": state.title,
                        "description": state.description,
                        "roadmap": slim_roadmap or state.roadmap,
                        "lessons_expected": state.lessons_expected or "",
                        "next_lesson_index": str(index),
                        "prev_lessons": prev_lessons,
                    }
                )
            count += 1

        if getattr(ai, "tool_calls", None):
            tracer.record(
                "warn",
                "tool budget exhausted; forcing final JSON output",
                index=index,
                rounds=count - 1,
                max_rounds=MAX_TOOL_CALLS_PER_AGENT,
            )
            self.logger.warning(f"Lesson Creator hit max tool calls: {MAX_TOOL_CALLS_PER_AGENT}")
            history.append(
                SystemMessage(
                    content=(
                        "Ngừng gọi công cụ ngay bây giờ. Hãy xuất JSON cuối cùng theo đúng schema yêu cầu, "
                        "dựa trên ngữ cảnh hiện có. Tuyệt đối không chèn thêm lời giải thích hay gọi công cụ."
                    )
                )
            )
            ai = self.chain.invoke(
                {
                    "id": state.id,
                    "history": history,
                    "difficulty": state.difficulty,
                    "duration": str(state.duration),
                    "title": state.title,
                    "description": state.description,
                    "roadmap": slim_roadmap or state.roadmap,
                    "lessons_expected": state.lessons_expected or "",
                    "next_lesson_index": str(index),
                    "prev_lessons": prev_lessons,
                }
            )

        # Parse JSON robustly and build a single Lesson
        try:
            json_content = json.loads(ai.content)
        except Exception as e:
            tracer.record("error", "failed to parse ai json", index=index, error=str(e))
            return None

        created = json_content.get("lessons") or []
        items = created if isinstance(created, list) else ([created] if created else [])
        if not items:
            # No lesson in response; create placeholder id
            lid = f"{state.id}-L{index}"
            tracer.record("warn", "no lessons in ai json; placeholder", index=index, lesson_id=lid)
            return Lesson(
                lesson_id=lid,
                title="Placeholder Lesson",
                overview="",
                content="",
                duration=30,
                assessments=None
            )

        obj = items[0]
        # Map from LLM response to new schema
        lesson_id = obj.get("lesson_id") or f"{state.id}-L{index}"
        title = obj.get("title") or obj.get("lesson_name") or f"Lesson {index}"
        overview = obj.get("overview") or obj.get("lesson_description") or ""
        content = obj.get("content") or obj.get("lesson_content") or ""
        duration = obj.get("duration") or 30
        
        # Parse assessments if present
        assessments_raw = obj.get("assessments") or []
        assessments = []
        for qa in assessments_raw:
            try:
                # Ensure answer is int
                answer = qa.get("answer")
                if isinstance(answer, str):
                    # Try to extract number from string like "1", "A", "option 1"
                    import re
                    match = re.search(r'\d+', str(answer))
                    answer = int(match.group()) if match else 1
                elif not isinstance(answer, int):
                    answer = 1
                
                # Validate answer range
                if not (1 <= answer <= 4):
                    answer = 1
                
                assessments.append({
                    "question": qa.get("question", ""),
                    "options": qa.get("options", []),
                    "answer": answer,
                    "hint": qa.get("hint", ""),
                    "explanation": qa.get("explanation", ""),
                    "difficulty": qa.get("difficulty", "medium")
                })
            except Exception as e:
                tracer.record("warn", "failed to parse assessment", error=str(e))
                continue
        
        # Basic validation
        if len(content) < 100:
            tracer.record("warn", "content too short", index=index, length=len(content))
        if len(assessments) < 3:
            tracer.record("warn", "too few assessments", index=index, count=len(assessments))
        
        lesson = Lesson(
            lesson_id=lesson_id,
            title=title,
            overview=overview,
            content=content,
            duration=duration,
            assessments=assessments if assessments else None
        )

        tracer.record("done", "single lesson generated", index=index, lesson_id=lesson.lesson_id, 
                     assessments_count=len(assessments))
