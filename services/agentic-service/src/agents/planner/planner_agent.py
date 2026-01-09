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

        # PROGRESSIVE RETRIEVAL: Execute 3-layer retrieval BEFORE LLM
        from agents.base.progressive_retrieval import execute_progressive_retrieval
        
        tracer.record("retrieval", "starting progressive 3-layer retrieval")
        
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
            context_title="",  # No title yet for planner
            k=5
        )
        
        self.logger.info(f"[PLANNER] Progressive retrieval: L1={retrieval_results['layer1_query'][:30]}... | L2={retrieval_results['layer2_query'][:30]}... | L3={retrieval_results['layer3_query'][:30]}...")
        
        # DEBUG: Dump FULL retrieved context to verify what LLM actually sees
        self.logger.info(f"[PLANNER] Retrieved context length: {len(retrieval_results['all_text'])} chars")
        self.logger.info(f"[PLANNER] ========== FULL RETRIEVED CONTEXT START ==========")
        self.logger.info(retrieval_results['all_text'])
        self.logger.info(f"[PLANNER] ========== FULL RETRIEVED CONTEXT END ==========")
        
        tracer.record("retrieval", "completed 3 layers", 
                     layer1_query=retrieval_results['layer1_query'],
                     layer2_query=retrieval_results['layer2_query'],
                     layer3_query=retrieval_results['layer3_query'],
                     context_length=len(retrieval_results['all_text']))
        
        # RADICAL FIX: Separate context from instruction
        # System message = Retrieved context (FACTS)
        # User message = Task instruction (WHAT TO DO)
        base_instruction = self.prompt_manager.get_prompt(self.name).format(
            id=state.id, history=[], difficulty=state.difficulty, duration=str(state.duration)
        )
        
        # System message: ONLY the retrieved context with STRONG emphasis
        context_message = SystemMessage(content=f"""
⚠️ CRITICAL: ONLY USE THIS RETRIEVED CONTENT ⚠️

Below is the RETRIEVED CONTENT from the user's uploaded document (3 layers of semantic search):

{retrieval_results['all_text']}

🔴 ABSOLUTE RULES:
1. This retrieved text is your ONLY source of truth
2. You CANNOT use external knowledge, pre-training, or examples
3. You MUST identify the MAIN TOPIC from this text ONLY
4. If the document discusses multiple topics (e.g., "Pathlight platform" + implementation details in "Python/Flask"), the MAIN TOPIC is the primary subject (Pathlight), NOT the tools used (Python/Flask)

🎯 YOUR TASK: Read this content and identify what subject this document is PRIMARILY about.
""")
        
        # User message: Task instruction with EXPLICIT main topic detection
        task_message = SystemMessage(content=base_instruction + """

🔥 CRITICAL EXECUTION STEPS 🔥

STEP 1: IDENTIFY MAIN TOPIC
- Read the retrieved content above carefully
- Determine: "What is this document PRIMARILY explaining or teaching?"
- Look for: Document title, abstract, most frequently discussed concepts, detailed technical explanations
- CRITICAL DISTINCTION: Main subject (what is being studied/built) vs Implementation details (tools/languages/frameworks used)

STEP 2: CREATE ROADMAP
- Course name MUST match the MAIN TOPIC from Step 1
- Lessons cover aspects of the MAIN TOPIC only
- Use 100% Vietnamese language
- Output valid JSON format

STEP 3: SELF-VALIDATE
- Re-read your course name
- Check: Does it match what the retrieved content is primarily about?
- If mismatch detected, regenerate the roadmap

Do NOT call any retrieval tools. Use ONLY the pre-loaded context above.
""")
        
        history: List = [context_message, task_message]

        # CHAIN-OF-THOUGHT FIX: Use structured schema to force step-by-step reasoning
        # Instead of jumping straight to roadmap, force LLM to:
        # 1. Identify main topic
        # 2. List key concepts
        # 3. Distinguish tools vs subject
        # 4. Then generate roadmap
        from langchain_openai import ChatOpenAI
        from constant import LLM_MAX_TOKENS_PLANNER, LLM_REQUEST_TIMEOUT
        from schemas.context import CourseAnalysis
        
        no_tools_llm = ChatOpenAI(
            model_name=self.foundation_model,
            openai_api_key=self.llm.openai_api_key,
            temperature=0.3,
            request_timeout=LLM_REQUEST_TIMEOUT,
            max_tokens=LLM_MAX_TOKENS_PLANNER
        )
        # Bind with Pydantic schema for structured output with reasoning
        structured_llm = no_tools_llm.with_structured_output(CourseAnalysis)
        
        # DEBUG: Log actual messages being sent to LLM
        self.logger.info(f"[PLANNER] ========== MESSAGES SENT TO LLM ==========")
        self.logger.info(f"[PLANNER] Message count: {len(history)}")
        for i, msg in enumerate(history):
            self.logger.info(f"[PLANNER] Message {i+1} type: {type(msg).__name__}")
            self.logger.info(f"[PLANNER] Message {i+1} content length: {len(msg.content)} chars")
            self.logger.info(f"[PLANNER] Message {i+1} first 200 chars: {msg.content[:200]}...")
        self.logger.info(f"[PLANNER] ========== END MESSAGES ==========")
        
        # Invoke with structured output - forces CoT reasoning
        analysis: CourseAnalysis = structured_llm.invoke(history)
        
        # Log reasoning steps for debugging
        self.logger.info(f"[PLANNER CoT] Main topic identified: {analysis.main_topic}")
        self.logger.info(f"[PLANNER CoT] Key concepts: {', '.join(analysis.key_concepts)}")
        self.logger.info(f"[PLANNER CoT] Implementation tools: {', '.join(analysis.implementation_tools)}")
        self.logger.info(f"[PLANNER CoT] Target audience: {analysis.target_audience}")
        tracer.record("cot_analysis", "reasoning completed",
                     main_topic=analysis.main_topic,
                     concepts_count=len(analysis.key_concepts),
                     tools_count=len(analysis.implementation_tools))
        
        # Convert CourseAnalysis to State format
        json_content = {
            "course_name": analysis.course_name,
            "course_description": analysis.course_description,
            "course_roadmap": [{"title": r.title, "description": r.description} for r in analysis.course_roadmap]
        }
        
        tracer.record("llm", "structured output with CoT", 
                     course_name=analysis.course_name,
                     roadmap_items=len(analysis.course_roadmap))
        
        # Validate required fields (Pydantic should enforce this, but double-check)
        if not analysis.course_name or not analysis.course_description or not analysis.course_roadmap:
            tracer.record("error", "incomplete structured output",
                         has_name=bool(analysis.course_name),
                         has_desc=bool(analysis.course_description),
                         roadmap_count=len(analysis.course_roadmap) if analysis.course_roadmap else 0)
            raise ValueError(
                f"Planner: Incomplete structured output - "
                f"name={bool(analysis.course_name)}, desc={bool(analysis.course_description)}, "
                f"roadmap={len(analysis.course_roadmap) if analysis.course_roadmap else 0}"
            )
        
        # Extract fields from structured output
        course_name = json_content["course_name"]
        course_description = json_content["course_description"]
        course_roadmap = json_content["course_roadmap"]
        
        # Validate roadmap
        if not course_roadmap or len(course_roadmap) == 0:
            tracer.record("error", "empty roadmap")
            self.logger.error(f"Planner validation failed: empty roadmap")
            
            # ULTIMATE FALLBACK: Create a basic roadmap based on duration
            self.logger.warning("Creating fallback roadmap due to empty LLM output")
            num_lessons = max(2, min(5, int(state.duration) // 20))
            course_roadmap = [
                {
                    "title": f"Module {i+1}: {course_name} - Part {i+1}",
                    "description": f"Learn key concepts and skills in this section of the course."
                }
                for i in range(num_lessons)
            ]
            tracer.record("warn", "using fallback roadmap", num_items=len(course_roadmap))
            self.logger.warning(f"Generated fallback roadmap with {len(course_roadmap)} items")
        
        # CRITICAL: Validate each roadmap item has "description" field
        for idx, item in enumerate(course_roadmap):
            if not isinstance(item, dict):
                self.logger.error(f"Roadmap item {idx} is not a dict: {item}")
                raise ValueError(f"Roadmap item {idx} must be a dictionary")
            
            if "description" not in item or not item.get("description"):
                self.logger.error(f"⚠️ ROADMAP ITEM {idx} MISSING DESCRIPTION!")
                self.logger.error(f"   Title: {item.get('title', 'NO TITLE')}")
                self.logger.error(f"   Item keys: {list(item.keys())}")
                # Add a generic description as fallback
                item["description"] = f"Chi tiết về {item.get('title', f'module {idx+1}')}"
                self.logger.warning(f"   → Added fallback description: {item['description']}")
        
        # Log all descriptions for debugging
        self.logger.info("=" * 60)
        self.logger.info("📋 ROADMAP DESCRIPTIONS VALIDATION:")
        for idx, item in enumerate(course_roadmap):
            desc = item.get("description", "")
            self.logger.info(f"  [{idx+1}] {item.get('title', 'NO TITLE')}")
            self.logger.info(f"      → Description ({len(desc)} chars): {desc[:100]}...")
        self.logger.info("=" * 60)
        
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