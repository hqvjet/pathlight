from dotenv import load_dotenv
load_dotenv()

from typing import List
import json
from agents.base.base_agent import BaseAgent
from agents.base.prompt_manager import PromptManager
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

from schemas.context import QuizState, QuizIdea
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
from core.logging import setup_logger
from core.tracing import StepTracer
from constant import MAX_TOOL_CALLS_PER_AGENT

MAX_HISTORY_MESSAGES = 10

def trim_history(history: List, max_messages: int = MAX_HISTORY_MESSAGES) -> List:
    """Keep only recent messages to prevent token explosion."""
    if len(history) <= max_messages:
        return history
    
    system_msg = history[0] if history and isinstance(history[0], SystemMessage) else None
    recent = history[-max_messages:]
    
    if system_msg and recent[0] != system_msg:
        return [system_msg] + recent
    return recent


class QuizPlannerAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        foundation_model: str,
        prompt_manager: PromptManager,
        llm_manager: LLMManager,
        tool_manager: ToolManager,
    ):
        """Initialize the QuizPlannerAgent."""
        super().__init__(name, foundation_model, prompt_manager)
        self.tool_manager = tool_manager
        self.tools = {t.name: t for t in tool_manager.get_tools(name)}
        
        from constant import LLM_MAX_TOKENS_PLANNER
        self.llm = llm_manager.get_llm(
            model_name=foundation_model,
            tools=list(self.tools.values()),
            max_tokens=LLM_MAX_TOKENS_PLANNER,
            enable_json_mode=True
        )
        self.chain = self.build_chain(self.llm)
        self.logger = setup_logger(__name__)

    def __call__(self, state: QuizState) -> QuizState:
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        tracer.record(
            "start",
            "invoke quiz planner",
            difficulty=state.difficulty,
            duration=state.duration,
            num_questions=state.num_questions,
        )

        history: List = [
            SystemMessage(
                content=self.prompt_manager.get_prompt(self.name).format(
                    id=state.id,
                    history=[],
                    difficulty=state.difficulty,
                    duration=str(state.duration),
                    num_questions=state.num_questions,
                )
            )
        ]

        ai: AIMessage = self.chain.invoke(
            {
                "id": state.id,
                "history": history,
                "difficulty": state.difficulty,
                "duration": str(state.duration),
                "num_questions": state.num_questions,
            }
        )
        history.append(ai)
        tracer.record("llm", "initial response", content_preview=str(ai.content)[:200])

        count = 1
        previous_queries_quiz = []
        query_keywords_quiz = set()
        
        def normalize_quiz_query(q: str) -> str:
            return " ".join(sorted(set(q.lower().split())))
        
        def get_quiz_keywords(q: str) -> set:
            stopwords = {'the', 'a', 'an', 'is', 'are', 'of', 'to', 'for', 'and', 'or', 'in', 'on', 'at', 'về', 'của', 'và', 'là'}
            return set(q.lower().split()) - stopwords
        
        while ai.tool_calls and count <= MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("tools", "llm requested tools", tool_calls=ai.tool_calls, iteration=count)
            
            # CRITICAL: Loop detection
            curr_queries_quiz = [tc.get("args", {}).get("query", "") for tc in ai.tool_calls]
            is_quiz_loop = False
            for cq in curr_queries_quiz:
                cq_norm = normalize_quiz_query(cq)
                cq_kw = get_quiz_keywords(cq)
                for prev in previous_queries_quiz:
                    if normalize_quiz_query(prev) == cq_norm:
                        is_quiz_loop = True
                        break
                if not is_quiz_loop and query_keywords_quiz:
                    overlap = len(cq_kw & query_keywords_quiz) / len(cq_kw) if cq_kw else 0
                    if overlap > 0.7:
                        is_quiz_loop = True
                query_keywords_quiz.update(cq_kw)
            
            if is_quiz_loop:
                self.logger.warning(f"QuizPlanner detected query loop at iteration {count}")
                tracer.record("warn", "query loop detected - forcing output", iteration=count)
                break
            
            previous_queries_quiz.extend(curr_queries_quiz)
            
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
                        "num_questions": state.num_questions,
                    }
                )
            count += 1

        # Force final JSON output if max tool calls reached
        if count > MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("warn", f"Hit max tool calls limit: {MAX_TOOL_CALLS_PER_AGENT}")
            self.logger.warning(f"QuizPlanner hit max tool calls: {MAX_TOOL_CALLS_PER_AGENT}")
            
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
                    "num_questions": state.num_questions,
                })
            except Exception as e:
                tracer.record("error", "final JSON invoke failed", error=str(e))
                raise ValueError(f"QuizPlanner: Failed to get final JSON output - {str(e)}")

        tracer.record("llm", "final response", content_preview=str(ai.content)[:200])
        
        # Validate content before parsing
        if not ai.content or not ai.content.strip():
            tracer.record("error", "empty content", has_tool_calls=bool(getattr(ai, 'tool_calls', None)))
            raise ValueError("QuizPlanner: LLM returned empty content")
        
        self.logger.debug(f"QuizPlanner LLM content (first 1000 chars): {ai.content[:1000]}")
        
        # Parse JSON
        try:
            json_content = json.loads(ai.content)
        except json.JSONDecodeError as e:
            tracer.record("error", "failed to parse JSON", error=str(e), content=str(ai.content)[:500])
            self.logger.error(f"QuizPlanner JSON parse error. Content: {ai.content[:1000]}")
            raise ValueError(f"QuizPlanner: Failed to parse LLM JSON response - {str(e)}")
        
        # Validate required fields
        quiz_title = json_content.get("quiz_title")
        if not quiz_title:
            tracer.record("error", "missing quiz_title", keys=list(json_content.keys()))
            raise ValueError("QuizPlanner: LLM response missing 'quiz_title' field")
        
        quiz_overview = json_content.get("quiz_overview")
        if not quiz_overview:
            tracer.record("error", "missing quiz_overview")
            raise ValueError("QuizPlanner: LLM response missing 'quiz_overview' field")
        
        quiz_ideas = json_content.get("quiz_ideas")
        if not quiz_ideas or not isinstance(quiz_ideas, list):
            tracer.record("error", "invalid quiz_ideas", type=type(quiz_ideas))
            raise ValueError("QuizPlanner: 'quiz_ideas' must be a list")
        
        # Validate ideas count matches num_questions
        if len(quiz_ideas) != state.num_questions:
            tracer.record("warn", "ideas count mismatch", expected=state.num_questions, got=len(quiz_ideas))
            # Adjust to match num_questions
            if len(quiz_ideas) < state.num_questions:
                raise ValueError(f"QuizPlanner: Expected {state.num_questions} ideas, got {len(quiz_ideas)}")
            else:
                quiz_ideas = quiz_ideas[:state.num_questions]
        
        # Convert to QuizIdea objects
        ideas = []
        for i, idea_data in enumerate(quiz_ideas):
            try:
                idea = QuizIdea(
                    topic=idea_data.get("topic", f"Topic {i+1}"),
                    description=idea_data.get("description", ""),
                    difficulty=idea_data.get("difficulty", state.difficulty),
                )
                ideas.append(idea)
            except Exception as e:
                tracer.record("error", f"Failed to parse idea {i}", error=str(e), data=idea_data)
                raise ValueError(f"QuizPlanner: Failed to parse idea {i}: {str(e)}")
        
        state.title = quiz_title
        state.overview = quiz_overview
        state.ideas = ideas
        state.ideas_expected = len(ideas)
        state.next_card_index = 0  # Start from first question
        
        tracer.record(
            "done",
            "quiz plan extracted",
            title=state.title,
            ideas_count=len(state.ideas),
        )
        
        return state
