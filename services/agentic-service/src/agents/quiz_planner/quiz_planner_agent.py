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
        
        # CoT: Build context and instruction messages
        base_instruction = self.prompt_manager.get_prompt(self.name).format(
            id=state.id,
            history=[],
            difficulty=state.difficulty,
            duration=str(state.duration),
            num_questions=state.num_questions,
            retrieved_context="",
        )
        
        context_msg = SystemMessage(content=f"""
⚠️ RETRIEVED CONTEXT FOR QUIZ GENERATION ⚠️

{retrieved_context}

Use ONLY this context to create quiz questions.
""")
        
        task_msg = SystemMessage(content=base_instruction + "\\n\\nAnalyze the retrieved context and create a quiz plan following the step-by-step reasoning process.")
        history: List = [context_msg, task_msg]
        
        # CoT: Use structured output instead of free-form JSON
        from langchain_openai import ChatOpenAI
        from constant import LLM_MAX_TOKENS_PLANNER, LLM_REQUEST_TIMEOUT
        from schemas.context import QuizPlanAnalysis
        
        cot_llm = ChatOpenAI(
            model_name=self.foundation_model,
            openai_api_key=self.llm.openai_api_key,
            temperature=0.3,
            request_timeout=LLM_REQUEST_TIMEOUT,
            max_tokens=LLM_MAX_TOKENS_PLANNER
        )
        structured_llm = cot_llm.with_structured_output(QuizPlanAnalysis)
        
        analysis: QuizPlanAnalysis = structured_llm.invoke(history)
        
        # Log CoT reasoning (minimal)
        self.logger.info(f"[QUIZ PLANNER CoT] Main topics: {', '.join(analysis.main_topics)}")
        tracer.record("cot_quiz_plan", "reasoning completed",
                     topics_count=len(analysis.main_topics),
                     ideas_count=len(analysis.quiz_ideas))
        tracer.record("llm", "CoT structured output",
                     title=analysis.quiz_title[:50] if analysis.quiz_title else "(no title)",
                     ideas_count=len(analysis.quiz_ideas))
        
        # Validate structured output
        if not analysis.quiz_title:
            tracer.record("error", "missing quiz_title")
            raise ValueError("QuizPlanner: Missing quiz_title in structured output")
        
        if not analysis.quiz_overview:
            tracer.record("error", "missing quiz_overview")
            raise ValueError("QuizPlanner: Missing quiz_overview in structured output")
        
        if not analysis.quiz_ideas or not isinstance(analysis.quiz_ideas, list):
            tracer.record("error", "invalid quiz_ideas", type=type(analysis.quiz_ideas))
            raise ValueError("QuizPlanner: quiz_ideas must be a list")
        
        # Validate ideas count matches num_questions
        if len(analysis.quiz_ideas) != state.num_questions:
            tracer.record("warn", "ideas count mismatch", expected=state.num_questions, got=len(analysis.quiz_ideas))
            if len(analysis.quiz_ideas) < state.num_questions:
                raise ValueError(f"QuizPlanner: Expected {state.num_questions} ideas, got {len(analysis.quiz_ideas)}")
            else:
                # Trim to match
                analysis.quiz_ideas = analysis.quiz_ideas[:state.num_questions]
        
        # Store in state
        state.title = analysis.quiz_title
        state.overview = analysis.quiz_overview
        state.ideas = analysis.quiz_ideas  # Already QuizIdea objects from Pydantic
        state.ideas_expected = len(analysis.quiz_ideas)
        state.next_card_index = 0
        state.retrieved_context = retrieved_context
        
        tracer.record(
            "done",
            "quiz plan extracted",
            title=state.title,
            ideas_count=len(state.ideas),
        )
        
        return state
