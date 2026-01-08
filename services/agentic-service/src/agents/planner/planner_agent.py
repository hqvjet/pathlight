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
        
        # Mark planning phase started
        try:
            status.mark_planning(state.id)
        except Exception:
            pass

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
        previous_queries = []  # Track queries to detect loops
        consecutive_same_query = 0  # Track consecutive identical queries
        
        while ai.tool_calls and count <= MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("tools", "llm requested tools", tool_calls=ai.tool_calls, iteration=count)
            
            # CRITICAL: Detect if LLM is stuck in loop (calling same query repeatedly)
            current_queries = [tc.get("args", {}).get("query", "") for tc in ai.tool_calls]
            
            # Check if ANY current query has been seen in last 3 queries
            if len(previous_queries) > 0:
                last_queries_set = set(previous_queries[-3:] if len(previous_queries) >= 3 else previous_queries)
                if any(q in last_queries_set for q in current_queries):
                    consecutive_same_query += 1
                    self.logger.warning(f"Planner repeating query (count={consecutive_same_query}) at iteration {count}")
                    tracer.record("warn", "query repetition detected", iteration=count, repetition_count=consecutive_same_query, query=current_queries[0][:100])
                    
                    # Force stop after 2 consecutive repetitions
                    if consecutive_same_query >= 2:
                        self.logger.warning(f"Planner stuck in loop after {consecutive_same_query} repetitions, forcing final output")
                        tracer.record("warn", "detected query loop - stopping", iteration=count)
                        break  # Exit loop to force final JSON output
                else:
                    consecutive_same_query = 0
            
            previous_queries.extend(current_queries)
            
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

        # CRITICAL FIX: Force final JSON output after hitting max tool calls OR detecting loop
        if count > MAX_TOOL_CALLS_PER_AGENT or (ai.tool_calls and len(ai.tool_calls) > 0):
            tracer.record("warn", f"Forcing final output (count={count}, max={MAX_TOOL_CALLS_PER_AGENT})")
            self.logger.warning(f"Planner forcing final output: count={count}/{MAX_TOOL_CALLS_PER_AGENT}")
            
            # Add VERY explicit instruction to force JSON output with available context
            # Remove any tool call messages from history to prevent confusion
            force_instruction = SystemMessage(
                content=(
                    "=== CRITICAL INSTRUCTION - MUST FOLLOW ==="
                    "\n\nSTOP using tools NOW. You have gathered enough context.\n\n"
                    "REQUIRED ACTION: Generate the final JSON output RIGHT NOW based on the information you have retrieved.\n\n"
                    "If the context is not detailed enough, create a GENERAL roadmap based on what you know.\n\n"
                    "You MUST output ONLY valid JSON in this exact format:\n"
                    "{{\n"
                    '  "course_name": "Course title from document or general topic",\n'
                    '  "course_description": "2-3 sentence description",\n'
                    '  "course_roadmap": [\n'
                    '    {{"title": "Module 1", "description": "Description"}},\n'
                    '    {{"title": "Module 2", "description": "Description"}},\n'
                    '    {{"title": "Module 3", "description": "Description"}}\n'
                    "  ]\n"
                    "}}\n\n"
                    "IMPORTANT: course_roadmap MUST contain at least 2-3 items.\n"
                    "DO NOT call any more tools. DO NOT add any text outside the JSON."
                )
            )
            history.append(force_instruction)
            
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
                    "history": history,
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
            
            # FALLBACK: Try to extract JSON from text if wrapped in markdown or has extra text
            import re
            json_match = re.search(r'\{[\s\S]*\}', ai.content)
            if json_match:
                try:
                    json_content = json.loads(json_match.group(0))
                    self.logger.warning("Successfully extracted JSON from wrapped content")
                except:
                    raise ValueError(f"Planner: Failed to parse LLM JSON response - {str(e)}")
            else:
                raise ValueError(f"Planner: Failed to parse LLM JSON response - {str(e)}")
        
        # CRITICAL FIX: Validate required fields with detailed error messages
        course_name = json_content.get("course_name")
        if not course_name:
            tracer.record("error", "missing course_name", keys=list(json_content.keys()))
            self.logger.error(f"Planner validation failed: missing course_name. JSON keys: {list(json_content.keys())}")
            self.logger.error(f"Full JSON content: {json_content}")
            raise ValueError(f"Planner: LLM response missing 'course_name' field. Available keys: {list(json_content.keys())}")
        
        course_description = json_content.get("course_description")
        if not course_description:
            tracer.record("error", "missing course_description")
            self.logger.error(f"Planner validation failed: missing course_description. JSON: {json_content}")
            raise ValueError(f"Planner: LLM response missing 'course_description' field. Available keys: {list(json_content.keys())}")
        
        course_roadmap = json_content.get("course_roadmap")
        if not course_roadmap or not isinstance(course_roadmap, list) or len(course_roadmap) == 0:
            tracer.record("error", "invalid course_roadmap", type=type(course_roadmap), value=course_roadmap)
            self.logger.error(f"Planner validation failed: invalid course_roadmap")
            self.logger.error(f"Type: {type(course_roadmap)}, Value: {course_roadmap}")
            self.logger.error(f"Full JSON: {json_content}")
            
            # ULTIMATE FALLBACK: Create a basic roadmap based on duration
            self.logger.warning("Creating fallback roadmap due to invalid LLM output")
            num_lessons = max(2, min(5, int(state.duration) // 20))  # 2-5 lessons based on duration
            course_roadmap = [
                {
                    "title": f"Module {i+1}: {course_name} - Part {i+1}",
                    "description": f"Learn key concepts and skills in this section of the course."
                }
                for i in range(num_lessons)
            ]
            tracer.record("warn", "using fallback roadmap", num_items=len(course_roadmap))
            self.logger.warning(f"Generated fallback roadmap with {len(course_roadmap)} items")
        
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
        # Initialize next_lesson_index to 1 (start from first lesson)
        state.next_lesson_index = 1
        
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