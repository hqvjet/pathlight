from dotenv import load_dotenv
load_dotenv()

from typing import List, Optional
import asyncio
import json
import os
from agents.base.base_agent import BaseAgent
from agents.base.prompt_manager import PromptManager
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

from schemas.context import State, Lesson
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
from core.logging import setup_logger
from core.tracing import StepTracer


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

    async def __call__(self, state: State) -> State:
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        tracer.record("start", "invoke lesson creator", difficulty=state.difficulty, duration=state.duration)

        lessons = state.lessons or []
        if state.lessons is None:
            state.lessons = lessons

        # Determine total planned lessons (if roadmap exists) and pick concurrency
        planned_total: Optional[int] = state.lessons_expected or (len(state.roadmap) if state.roadmap else None)
        concurrency = int(os.getenv("LESSON_CREATOR_CONCURRENCY", "3"))

        # If we know how many lessons to make, try to parallelize a batch
        if planned_total and len(lessons) < planned_total:
            start_index = len(lessons) + 1
            # next batch of indices to generate
            indices = list(range(start_index, min(planned_total, start_index + concurrency - 1) + 1))
            tracer.record("batch", "generate lessons concurrently", indices=indices)
            prev_ids = [l.lesson_id for l in lessons]

            # Launch concurrent generation for this batch
            tasks = [self._generate_single_lesson(state, i, prev_ids) for i in indices]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            new_lessons: List[Lesson] = []
            for idx, res in zip(indices, results):
                if isinstance(res, Exception):
                    # On failure, add a placeholder to keep progress moving
                    lid = f"{state.id}-L{idx}"
                    tracer.record("error", "lesson generation failed; placeholder used", index=idx, error=str(res))
                    new_lessons.append(Lesson(lesson_id=lid))
                elif res is None:
                    lid = f"{state.id}-L{idx}"
                    tracer.record("warn", "lesson generation returned None; placeholder used", index=idx)
                    new_lessons.append(Lesson(lesson_id=lid))
                else:
                    new_lessons.append(res)

            # Append in order to keep deterministic ordering
            lessons.extend(new_lessons)
            state.next_lesson_index = (indices[-1] + 1) if indices else (len(lessons) + 1)
            tracer.record("done", "batch lessons appended", count=len(new_lessons), last_index=state.next_lesson_index)
            return state

        # Fallback to single-lesson path when total is unknown
        next_index = state.next_lesson_index or (len(lessons) + 1)
        result = await self._generate_single_lesson(state, next_index, [l.lesson_id for l in lessons])
        if result is None:
            lid = f"{state.id}-L{next_index}"
            lessons.append(Lesson(lesson_id=lid))
        else:
            lessons.append(result)
        state.next_lesson_index = next_index + 1
        tracer.record("done", "single lesson appended", lesson_id=lessons[-1].lesson_id, next_index=state.next_lesson_index)
        return state

    async def _generate_single_lesson(self, state: State, index: int, prev_lessons: List[str]) -> Optional[Lesson]:
        """Generate one lesson for the given index, with tool-call loop and robust JSON parsing."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        max_tool_rounds = int(os.getenv("AGENT_TOOL_MAX_ROUNDS", "10"))

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

        ai: AIMessage = await self.chain.ainvoke(
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
        while getattr(ai, "tool_calls", None) and count <= max_tool_rounds:
            tracer.record("tools", "llm requested tools", index=index, tool_calls=ai.tool_calls)
            for tool_call in ai.tool_calls:
                tool_name = tool_call["name"]
                tool_call_id = tool_call["id"]
                args = tool_call["args"]
                if tool_name not in self.tools:
                    raise ValueError(f"Tool {tool_name} not found in tools.")

                result = await self.tool_manager.execute_tool(tool_name, args)
                history.append(
                    ToolMessage(tool_call_id=tool_call_id, name=tool_name, content=result)
                )
                tracer.record(
                    "tool_result",
                    f"{tool_name} executed",
                    index=index,
                    args=args,
                    result_preview=str(result)[:200],
                )

                ai = await self.chain.ainvoke(
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
                max_rounds=max_tool_rounds,
            )
            history.append(
                SystemMessage(
                    content=(
                        "Ngừng gọi công cụ ngay bây giờ. Hãy xuất JSON cuối cùng theo đúng schema yêu cầu, "
                        "dựa trên ngữ cảnh hiện có. Tuyệt đối không chèn thêm lời giải thích hay gọi công cụ."
                    )
                )
            )
            ai = await self.chain.ainvoke(
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
            return Lesson(lesson_id=lid)

        obj = items[0]
        if isinstance(obj, dict) and ("lesson_name" in obj or "lesson_description" in obj or "lesson_content" in obj):
            lesson = Lesson(
                lesson_id=obj.get("lesson_id") or f"{state.id}-L{index}",
                lesson_name=obj.get("lesson_name"),
                lesson_description=obj.get("lesson_description"),
                lesson_content=obj.get("lesson_content"),
            )
        elif isinstance(obj, dict) and "lesson_id" in obj:
            lesson = Lesson(lesson_id=obj["lesson_id"])
        else:
            # Fallback: generate synthetic id
            lesson = Lesson(lesson_id=f"{state.id}-L{index}")

        tracer.record("done", "single lesson generated", index=index, lesson_id=lesson.lesson_id)
        return lesson