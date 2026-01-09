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

        # PROGRESSIVE RETRIEVAL: Execute 3-layer retrieval BEFORE LLM (like course planner)
        from agents.base.progressive_retrieval import execute_progressive_retrieval
        
        tracer.record("retrieval", "starting progressive 3-layer retrieval for quiz")
        
        # Create retrieval function wrapper
        def retrieval_func(query: str, material_id: str, k: int = 5):
            tool = self.tools.get("retrieval_tool")
            if not tool:
                raise ValueError("retrieval_tool not found!")
            result = tool._run(id=material_id, query=query, k=k)
            return result
        
        # Execute progressive retrieval
        retrieval_results = execute_progressive_retrieval(
            retrieval_tool_func=retrieval_func,
            material_id=state.id,
            context_title="",  # No specific context for quiz planner
            k=5
        )
        
        self.logger.info(f"[QUIZ PLANNER] Progressive retrieval: L1={retrieval_results['layer1_query'][:30]}... | L2={retrieval_results['layer2_query'][:30]}... | L3={retrieval_results['layer3_query'][:30]}...")
        tracer.record("retrieval", "completed 3 layers", 
                     layer1_query=retrieval_results['layer1_query'],
                     layer2_query=retrieval_results['layer2_query'],
                     layer3_query=retrieval_results['layer3_query'])
        
        # Format retrieved context
        retrieved_context = retrieval_results['all_text']
        
        # Build initial prompt WITH retrieval results pre-loaded
        initial_prompt = self.prompt_manager.get_prompt(self.name).format(
            id=state.id,
            history=[],
            difficulty=state.difficulty,
            duration=str(state.duration),
            num_questions=state.num_questions,
            retrieved_context=retrieved_context,
        )

        history: List = [SystemMessage(content=initial_prompt)]

        ai: AIMessage = self.chain.invoke(
            {
                "id": state.id,
                "history": history,
                "difficulty": state.difficulty,
                "duration": str(state.duration),
                "num_questions": state.num_questions,
                "retrieved_context": retrieved_context,
            }
        )
        history.append(ai)
        tracer.record("llm", "initial response", content_preview=str(ai.content)[:200])

        # FORCE JSON OUTPUT if LLM tries to call tools despite having retrieval context
        if ai.tool_calls:
            self.logger.warning("QuizPlanner called tools despite having retrieval context. Forcing JSON output.")
            tracer.record("warn", "llm called tools despite pre-loaded context - forcing JSON")
            
            # Remove tools and force JSON
            force_instruction = SystemMessage(
                content=(
                    "You already have ALL retrieval context above. "
                    "DO NOT call any more tools. Output ONLY the quiz plan JSON now:\n"
                    '{"quiz_title": "...", "quiz_overview": "...", "quiz_ideas": [...]}'
                )
            )
            history.append(force_instruction)
            
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
                    "retrieved_context": retrieved_context,
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
        state.retrieved_context = retrieved_context  # Store context for questioner to reuse
        
        tracer.record(
            "done",
            "quiz plan extracted",
            title=state.title,
            ideas_count=len(state.ideas),
        )
        
        return state
