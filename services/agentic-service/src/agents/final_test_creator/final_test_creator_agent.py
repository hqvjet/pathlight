from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any
import json
from agents.base.base_agent import BaseAgent
from agents.base.prompt_manager import PromptManager
from langchain_core.messages import SystemMessage, AIMessage

from schemas.context import State, Lesson, TestQA
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
from core.logging import setup_logger
from core.tracing import StepTracer
from core import status_tracker as status


class FinalTestCreatorAgent(BaseAgent):
    """Aggregate per-lesson tests into a single final test.

    Strategy:
    - Provide lessons and in-memory tests_content to the model.
    - Ask it to synthesize a balanced final exam (MCQ) across all lessons.
    - Return a JSON with final_test: [ { question, options, answer, explaination } ]
    """

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
        self.tools = {t.name: t for t in tool_manager.get_tools(name)} if hasattr(tool_manager, "get_tools") else {}
        self.llm = llm_manager.get_llm(model_name=foundation_model, tools=list(self.tools.values()))
        self.chain = self.build_chain(self.llm)
        self.logger = setup_logger(__name__)

    async def __call__(self, state: State) -> State:
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        tracer.record("start", "invoke final test creator", lessons=len(state.lessons or []))

        lessons_payload: List[Dict[str, Any]] = []
        for lesson in (state.lessons or []):
            lessons_payload.append(
                {
                    "lesson_id": lesson.lesson_id,
                    "lesson_name": getattr(lesson, "lesson_name", None),
                    "tests": [t.model_dump() for t in (lesson.tests or [])],
                }
            )

        # If we don't have any tests_content, we can still ask the model to sample across lesson metadata
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
        tracer.record("llm", "final exam draft", content_preview=str(ai.content)[:200])

        try:
            data = json.loads(ai.content)
        except Exception as e:
            tracer.record("error", "failed to parse ai json", error=str(e))
            return state

        final_test = data.get("final_test") or []
        # Coerce items to TestQA model shape
        coerced: List[TestQA] = []
        for item in final_test:
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
                d = item if isinstance(item, dict) else {}
                coerced.append(TestQA(
                    question=str(d.get("question", "")),
                    options=list(d.get("options", []))[:4],
                    answer=str(d.get("answer", "")),
                    explaination=str(d.get("explaination", "")),
                ))
        state.final_test = coerced

        tracer.record("done", "final test attached", count=len(coerced))
        try:
            status.mark_final_ready(state.id, len(coerced))
        except Exception:
            pass
        return state