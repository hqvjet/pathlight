from dotenv import load_dotenv
load_dotenv()

from typing import List, Optional
import asyncio
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

    async def __call__(self, state: State) -> State:
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        tracer.record("start", "invoke test creator", lessons=len(state.lessons or []))
        if not state.lessons:
            tracer.record("skip", "no lessons found in state")
            return state

        # Pick lessons that still need tests
        target_lessons = [l for l in state.lessons if not getattr(l, "tests", None)]
        if not target_lessons:
            tracer.record("skip", "all lessons already have tests")
            return state

        concurrency = int(os.getenv("TEST_CREATOR_CONCURRENCY", "4"))
        tracer.record("batch", "generate tests concurrently", targets=len(target_lessons), concurrency=concurrency)

        # Launch per-lesson test generation
        tasks = [self._generate_single_lesson_tests(state, lesson) for lesson in target_lessons]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures = 0
        for lesson, res in zip(target_lessons, results):
            if isinstance(res, Exception):
                failures += 1
                tracer.record("error", "test generation failed", lesson_id=lesson.lesson_id, error=str(res))

        tracer.record("done", "tests generation completed", failures=failures)
        try:
            # If all lessons have tests now, mark lessons_ready
            if all(getattr(l, "tests", None) for l in state.lessons or []):
                status.mark_lessons_ready(state.id, len(state.lessons or []))
        except Exception:
            pass
        return state

    async def _generate_single_lesson_tests(self, state: State, lesson) -> None:
        """Generate tests for a single lesson, with tool-call cap and forced finalization."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        max_tool_rounds = int(os.getenv("AGENT_TOOL_MAX_ROUNDS", "10"))

        content = getattr(lesson, "lesson_content", None)
        if isinstance(content, str) and len(content) > 800:
            preview = content[:800] + "…"
        else:
            preview = content

        lessons_payload = [
            {
                "lesson_id": lesson.lesson_id,
                "lesson_name": getattr(lesson, "lesson_name", None),
                "lesson_description": getattr(lesson, "lesson_description", None),
                "lesson_content": preview,
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

        ai: AIMessage = await self.chain.ainvoke(
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
        while getattr(ai, "tool_calls", None) and count <= max_tool_rounds:
            tracer.record("tools", "llm requested tools", lesson_id=lesson.lesson_id, tool_calls=ai.tool_calls)
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
                    lesson_id=lesson.lesson_id,
                    args=args,
                    result_preview=str(result)[:200],
                )

                ai = await self.chain.ainvoke(
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
                max_rounds=max_tool_rounds,
            )
            history.append(
                SystemMessage(
                    content=(
                        "Dừng gọi công cụ ngay. Hãy xuất JSON cuối cùng với trường tests theo schema, không thêm giải thích."
                    )
                )
            )
            ai = await self.chain.ainvoke(
                {
                    "id": state.id,
                    "history": history,
                    "difficulty": state.difficulty,
                    "duration": str(state.duration),
                    "lessons": lessons_payload,
                }
            )

        # Parse response, accept map keyed by lesson_id or a direct list under tests
        try:
            json_content = json.loads(ai.content)
        except Exception as e:
            tracer.record("error", "failed to parse ai json", lesson_id=lesson.lesson_id, error=str(e))
            return

        tests_payload = json_content.get("tests")
        arr: Optional[List] = None
        if isinstance(tests_payload, dict):
            arr = tests_payload.get(lesson.lesson_id)
        elif isinstance(tests_payload, list):
            arr = tests_payload

        if arr and isinstance(arr, list):
            # Coerce items to TestQA model shape
            coerced: List[TestQA] = []
            for item in arr:
                try:
                    if isinstance(item, dict):
                        coerced.append(TestQA(**item))
                    else:
                        coerced.append(TestQA(
                            question=str(item),
                            options=[],
                            answer="",
                            explaination="",
                        ))
                except Exception:
                    # Best-effort coercion for malformed dicts
                    d = item if isinstance(item, dict) else {}
                    coerced.append(TestQA(
                        question=str(d.get("question", "")),
                        options=list(d.get("options", []))[:4],
                        answer=str(d.get("answer", "")),
                        explaination=str(d.get("explaination", "")),
                    ))
            lesson.tests = coerced
            tracer.record("done", "tests attached", lesson_id=lesson.lesson_id, count=len(coerced))
        else:
            tracer.record("warn", "no tests returned for lesson", lesson_id=lesson.lesson_id)
