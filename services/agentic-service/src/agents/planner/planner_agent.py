from dotenv import load_dotenv
load_dotenv()

from typing import List
import json
from agents.base.base_agent import BaseAgent
from agents.base.prompt_manager import PromptManager
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

from schemas.context import State
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


class PlannerAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        foundation_model: str,
        prompt_manager: PromptManager,
        llm_manager: LLMManager,
        tool_manager: ToolManager,
    ):
        """Initialize the PlannerAgent."""
        super().__init__(name, foundation_model, prompt_manager)
        # Keep references to tools and llm so we can execute tool calls in a loop
        self.tool_manager = tool_manager
        self.tools = {t.name: t for t in tool_manager.get_tools(name)}
        self.llm = llm_manager.get_llm(
            model_name=foundation_model, tools=list(self.tools.values())
        )
        self.chain = self.build_chain(self.llm)
        self.logger = setup_logger(__name__)

    def __call__(self, state: State) -> State:
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        tracer.record(
            "start",
            "invoke planner",
            difficulty=state.difficulty,
            duration=state.duration,
        )

        history: List = [
            SystemMessage(
                content=self.prompt_manager.get_prompt(self.name).format(
                    id=state.id, history=[], difficulty=state.difficulty, duration=str(state.duration)
                )
            )
        ]

        ai: AIMessage = self.chain.invoke(
            {
                "id": state.id,
                "history": history,
                "difficulty": state.difficulty,
                "duration": str(state.duration),
            }
        )
        history.append(ai)
        tracer.record("llm", "initial response", content_preview=str(ai.content)[:200])

        count = 1
        while ai.tool_calls and count <= MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("tools", "llm requested tools", tool_calls=ai.tool_calls, iteration=count)
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
                    args=args,
                    result_preview=str(result)[:200],
                )

                ai = self.chain.invoke(
                    {
                        "id": state.id,
                        "history": history,
                        "difficulty": state.difficulty,
                        "duration": str(state.duration),
                    }
                )
            count += 1

        if count > MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("warn", f"Hit max tool calls limit: {MAX_TOOL_CALLS_PER_AGENT}")
            self.logger.warning(f"Planner hit max tool calls: {MAX_TOOL_CALLS_PER_AGENT}")

        tracer.record("llm", "final response", content_preview=str(ai.content)[:200])
        json_content = json.loads(ai.content)
        state.title = json_content.get("course_name")
        state.description = json_content.get("course_description")
        state.roadmap = json_content.get("course_roadmap")
        
        # Set lessons_expected based on roadmap length
        if state.roadmap:
            state.lessons_expected = len(state.roadmap)
        
        tracer.record(
            "done", "plan extracted", 
            title=state.title, 
            roadmap_len=len(state.roadmap or []),
            lessons_expected=state.lessons_expected
        )
        try:
            status.mark_plan_ready(state.id, state.title, state.description, len(state.roadmap or []))
        except Exception:
            pass
        return state