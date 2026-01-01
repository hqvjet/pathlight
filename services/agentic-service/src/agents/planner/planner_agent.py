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
from constant import MAX_TOOL_CALLS_PER_AGENT, MIN_ROADMAP_ITEMS, MAX_ROADMAP_ITEMS

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
        # CRITICAL FIX: Planner needs NO max_tokens limit to output full roadmap JSON
        from constant import LLM_MAX_TOKENS_PLANNER
        self.llm = llm_manager.get_llm(
            model_name=foundation_model, 
            tools=list(self.tools.values()),
            max_tokens=LLM_MAX_TOKENS_PLANNER,
            enable_json_mode=True  # CRITICAL: Enable JSON mode
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

        # CRITICAL FIX: Force final JSON output after hitting max tool calls
        if count > MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("warn", f"Hit max tool calls limit: {MAX_TOOL_CALLS_PER_AGENT}")
            self.logger.warning(f"Planner hit max tool calls: {MAX_TOOL_CALLS_PER_AGENT}")
            # CRITICAL: Create LLM WITHOUT tools binding to prevent further tool calls
            # JSON mode is still enabled, so output will be JSON
            from langchain_openai import ChatOpenAI
            from constant import LLM_MAX_TOKENS_PLANNER, LLM_REQUEST_TIMEOUT
            final_llm = ChatOpenAI(
                model_name=self.foundation_model,
                openai_api_key=self.llm.openai_api_key,
                temperature=0.3,
                request_timeout=LLM_REQUEST_TIMEOUT,
                max_tokens=LLM_MAX_TOKENS_PLANNER,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
            final_chain = self.build_chain(final_llm)
            
            try:
                ai = final_chain.invoke({
                    "id": state.id,
                    "history": history,  # Use existing history, no modification
                    "difficulty": state.difficulty,
                    "duration": str(state.duration),
                })
            except Exception as e:
                tracer.record("error", "final JSON invoke failed", error=str(e))
                raise ValueError(f"Planner: Failed to get final JSON output - {str(e)}")

        tracer.record("llm", "final response", content_preview=str(ai.content)[:200])
        
        # CRITICAL FIX: Validate content before parsing
        if not ai.content or not ai.content.strip():
            tracer.record("error", "empty content", has_tool_calls=bool(getattr(ai, 'tool_calls', None)))
            raise ValueError(
                f"Planner: LLM returned empty content. "
                f"Has tool_calls: {bool(getattr(ai, 'tool_calls', None))}"
            )
        
        # Log full content for debugging
        self.logger.debug(f"Planner LLM content (first 1000 chars): {ai.content[:1000]}")
        
        # CRITICAL FIX: Strict JSON parsing with validation
        try:
            json_content = json.loads(ai.content)
        except json.JSONDecodeError as e:
            tracer.record("error", "failed to parse JSON", error=str(e), content=str(ai.content)[:500])
            self.logger.error(f"Planner JSON parse error. Content: {ai.content[:1000]}")
            raise ValueError(f"Planner: Failed to parse LLM JSON response - {str(e)}")
        
        # CRITICAL FIX: Validate required fields
        course_name = json_content.get("course_name")
        if not course_name:
            tracer.record("error", "missing course_name", keys=list(json_content.keys()))
            raise ValueError("Planner: LLM response missing 'course_name' field")
        
        course_description = json_content.get("course_description")
        if not course_description:
            tracer.record("error", "missing course_description")
            raise ValueError("Planner: LLM response missing 'course_description' field")
        
        course_roadmap = json_content.get("course_roadmap")
        if not course_roadmap or not isinstance(course_roadmap, list) or len(course_roadmap) == 0:
            tracer.record("error", "invalid course_roadmap", type=type(course_roadmap))
            raise ValueError("Planner: 'course_roadmap' must be non-empty list")
        
        # CRITICAL FIX: Validate roadmap length
        roadmap_len = len(course_roadmap)
        if roadmap_len < MIN_ROADMAP_ITEMS:
            tracer.record("error", "roadmap too short", count=roadmap_len, min=MIN_ROADMAP_ITEMS)
            raise ValueError(f"Planner: roadmap must have at least {MIN_ROADMAP_ITEMS} items, got {roadmap_len}")
        
        if roadmap_len > MAX_ROADMAP_ITEMS:
            tracer.record("warn", "roadmap too long, truncating", count=roadmap_len, max=MAX_ROADMAP_ITEMS)
            course_roadmap = course_roadmap[:MAX_ROADMAP_ITEMS]
            roadmap_len = len(course_roadmap)
        
        state.title = course_name
        state.description = course_description
        state.roadmap = course_roadmap
        
        # Set lessons_expected based on roadmap length
        state.lessons_expected = len(state.roadmap)
        
        tracer.record(
            "done", "plan extracted", 
            title=state.title, 
            roadmap_len=len(state.roadmap),
            lessons_expected=state.lessons_expected
        )
        try:
            status.mark_plan_ready(state.id, state.title, state.description, len(state.roadmap))
        except Exception:
            pass
        return state