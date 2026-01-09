from dotenv import load_dotenv
load_dotenv()

from typing import List, Optional
import json
import os
import asyncio
from agents.base.base_agent import BaseAgent
from agents.base.prompt_manager import PromptManager
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

from schemas.context import State, Lesson
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
from core.logging import setup_logger
from core.tracing import StepTracer
from core import status_tracker as status
from constant import MAX_TOOL_CALLS_PER_AGENT
from agents.lesson_creator.parallel_helper import generate_lessons_parallel

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
        # STABLE FIX: Use gpt-4o-mini with JSON mode
        # Reliable model + strict JSON = no more parsing errors
        from constant import LLM_MAX_TOKENS_LESSON
        self.llm = llm_manager.get_llm(
            model_name=foundation_model, 
            tools=list(self.tools.values()),
            max_tokens=LLM_MAX_TOKENS_LESSON,
            enable_json_mode=True  # CRITICAL: Enable JSON mode for reliable output
        )
        self.chain = self.build_chain(self.llm)
        self.logger = setup_logger(__name__)

    def __call__(self, state: State) -> State:
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        tracer.record("start", "invoke lesson creator", difficulty=state.difficulty, duration=state.duration)

        lessons = state.lessons or []
        if state.lessons is None:
            state.lessons = lessons

        # Determine total planned lessons
        planned_total: Optional[int] = state.lessons_expected or (len(state.roadmap) if state.roadmap else None)
        
        # Get current lesson title from roadmap if available for better context
        current_lesson_title = ""
        next_idx = state.next_lesson_index or (len(lessons) + 1)
        if state.roadmap and len(state.roadmap) >= next_idx:
            try:
                # Adjust index (roadmap is 0-indexed, next_lesson_index is 1-indexed usually)
                roadmap_idx = next_idx - 1
                if 0 <= roadmap_idx < len(state.roadmap):
                    # Roadmap items are Pydantic objects, not dicts
                    current_lesson_title = state.roadmap[roadmap_idx].title
            except:
                pass

        # SEQUENTIAL GENERATION - CRITICAL FIX for timeout
        # Generate ONE lesson at a time to prevent timeout and ensure quality
        if planned_total and len(lessons) < planned_total:
            # Use next_lesson_index from state (initialized by planner)
            start_index = state.next_lesson_index or (len(lessons) + 1)
            tracer.record("single", "generate next lesson (sequential)", index=start_index, total=planned_total, current_title=current_lesson_title)
            prev_ids = [l.lesson_id for l in lessons]

            result = self._generate_single_lesson(state, start_index, prev_ids)
            if result is None:
                # CRITICAL: Thất bại → raise error thay vì placeholder
                raise ValueError(f"Failed to generate lesson {start_index}: LLM returned None or invalid JSON")
            else:
                lessons.append(result)

            # Update index for next iteration
            state.next_lesson_index = start_index + 1
            tracer.record("done", "lesson appended", lesson_id=lessons[-1].lesson_id, next_index=state.next_lesson_index)
            # Track progress AFTER successfully creating lesson
            try:
                lessons_list = [{"id": l.lesson_id, "title": l.title} for l in lessons]
                status.update_lessons(state.id, status="processing", completed=len(lessons), total=planned_total, lessons=lessons_list)
            except Exception:
                pass
            return state

        # Fallback when total is unknown
        next_index = state.next_lesson_index or (len(lessons) + 1)
        result = self._generate_single_lesson(state, next_index, [l.lesson_id for l in lessons])
        if result is None:
            raise ValueError(f"Failed to generate lesson {next_index}: LLM returned None or invalid JSON")
        else:
            lessons.append(result)
        state.next_lesson_index = next_index + 1
        tracer.record("done", "single lesson appended", lesson_id=lessons[-1].lesson_id, next_index=state.next_lesson_index)
        try:
            planned = planned_total or len(state.roadmap or []) if 'planned_total' in locals() else len(state.roadmap or [])
            lessons_list = [{"id": l.lesson_id, "title": l.title} for l in lessons]
            status.update_lessons(state.id, status="processing", completed=len(lessons), total=planned, lessons=lessons_list)
        except Exception:
            pass
        return state

    def _generate_all_lessons(self, state: State, count: int) -> Optional[List[Lesson]]:
        """Generate ALL lessons at once for speed (batch mode)."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        
        history: List = [
            SystemMessage(
                content=self.prompt_manager.get_prompt(self.name).format(
                    id=state.id,
                    history=[],
                    difficulty=state.difficulty,
                    duration=str(state.duration),
                    title=state.title,
                    description=state.description,
                    roadmap=state.roadmap,
                    lessons_expected=count,
                    next_lesson_index="all",  # Signal to generate all
                    prev_lessons=[],
                )
            )
        ]

        ai: AIMessage = self.chain.invoke(
            {
                "id": state.id,
                "history": history,
                "difficulty": state.difficulty,
                "duration": str(state.duration),
                "title": state.title,
                "description": state.description,
                "roadmap": state.roadmap,
                "lessons_expected": count,
                "next_lesson_index": "all",
                "prev_lessons": [],
            }
        )
        tracer.record("llm", "batch initial response", content_preview=str(ai.content)[:200])

        iteration = 1
        previous_queries_batch = []  # Track queries for loop detection
        query_keywords_seen_batch = set()
        
        def normalize_query_batch(q: str) -> str:
            return " ".join(sorted(set(q.lower().split())))
        
        def get_query_keywords_batch(q: str) -> set:
            stopwords = {'the', 'a', 'an', 'is', 'are', 'of', 'to', 'for', 'and', 'or', 'in', 'on', 'at', 'về', 'của', 'và', 'là'}
            return set(q.lower().split()) - stopwords
        
        while getattr(ai, "tool_calls", None) and iteration <= MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("tools", "batch llm requested tools", tool_calls=ai.tool_calls, iteration=iteration)
            
            # CRITICAL: Check for query loops before executing
            current_queries_batch = [tc.get("args", {}).get("query", "") for tc in ai.tool_calls]
            is_loop = False
            
            for cq in current_queries_batch:
                cq_norm = normalize_query_batch(cq)
                cq_kw = get_query_keywords_batch(cq)
                
                for prev in previous_queries_batch:
                    if normalize_query_batch(prev) == cq_norm:
                        is_loop = True
                        break
                
                if not is_loop and query_keywords_seen_batch:
                    overlap = len(cq_kw & query_keywords_seen_batch) / len(cq_kw) if cq_kw else 0
                    if overlap > 0.7:
                        is_loop = True
                
                query_keywords_seen_batch.update(cq_kw)
            
            if is_loop:
                self.logger.warning(f"Batch lesson creator detected query loop at iteration {iteration}")
                tracer.record("warn", "batch query loop detected - forcing output", iteration=iteration)
                break
            
            previous_queries_batch.extend(current_queries_batch)
            
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
                        "title": state.title,
                        "description": state.description,
                        "roadmap": state.roadmap,
                        "lessons_expected": count,
                        "next_lesson_index": "all",
                        "prev_lessons": [],
                    }
                )
            iteration += 1

        if getattr(ai, "tool_calls", None):
            tracer.record("warn", "batch tool budget exhausted", rounds=iteration - 1)
            history.append(
                SystemMessage(
                    content="Ngừng gọi công cụ. Xuất JSON cuối cùng với tất cả lessons theo schema."
                )
            )
            ai = self.chain.invoke(
                {
                    "id": state.id,
                    "history": history,
                    "difficulty": state.difficulty,
                    "duration": str(state.duration),
                    "title": state.title,
                    "description": state.description,
                    "roadmap": state.roadmap,
                    "lessons_expected": count,
                    "next_lesson_index": "all",
                    "prev_lessons": [],
                }
            )

        # Parse all lessons from response
        try:
            json_content = json.loads(ai.content)
        except Exception as e:
            tracer.record("error", "batch failed to parse json", error=str(e))
            return None

        lessons_data = json_content.get("lessons") or []
        if not isinstance(lessons_data, list):
            lessons_data = [lessons_data] if lessons_data else []
        
        if not lessons_data:
            tracer.record("warn", "batch no lessons in response")
            return None

        # Parse each lesson
        lessons = []
        for idx, obj in enumerate(lessons_data, 1):
            lesson_id = obj.get("lesson_id") or f"{state.id}-L{idx}"
            title = obj.get("title") or obj.get("lesson_name") or f"Lesson {idx}"
            overview = obj.get("overview") or obj.get("lesson_description") or ""
            content = obj.get("content") or obj.get("lesson_content") or ""
            duration = obj.get("duration") or 30
            
            # Parse assessments if present
            assessments_raw = obj.get("assessments") or []
            assessments = []
            for qa in assessments_raw:
                try:
                    answer = qa.get("answer")
                    if isinstance(answer, str):
                        import re
                        match = re.search(r'\d+', str(answer))
                        answer = int(match.group()) if match else 1
                    elif not isinstance(answer, int):
                        answer = 1
                    
                    if not (1 <= answer <= 4):
                        answer = 1
                    
                    assessments.append({
                        "question": qa.get("question", ""),
                        "options": qa.get("options", []),
                        "answer": answer,
                        "hint": qa.get("hint", ""),
                        "explanation": qa.get("explanation", ""),
                        "difficulty": qa.get("difficulty", "medium")
                    })
                except Exception as e:
                    tracer.record("warn", f"lesson {idx}: failed to parse assessment", error=str(e))
                    continue
            
            lesson = Lesson(
                lesson_id=lesson_id,
                title=title,
                overview=overview,
                content=content,
                duration=duration,
                assessments=assessments if assessments else None
            )
            lessons.append(lesson)

        tracer.record("done", "batch generated", count=len(lessons))
        return lessons

    def _generate_single_lesson(self, state: State, index: int, prev_lessons: List[str]) -> Optional[Lesson]:
        """Generate one lesson for the given index, with progressive retrieval and robust JSON parsing."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)

        # Keep roadmap minimal: only the current item to reduce tokens
        # CRITICAL: Pass the specific title AND description of the lesson to be generated
        target_lesson_title = f"Lesson {index}"
        target_lesson_description = ""
        slim_roadmap = None
        if state.roadmap:
            # Try to get the specific roadmap item for this lesson
            roadmap_index = index - 1
            if 0 <= roadmap_index < len(state.roadmap):
                 try:
                    target_item = state.roadmap[roadmap_index]
                    # Roadmap items are Pydantic objects, not dicts
                    slim_roadmap = [target_item]
                    target_lesson_title = target_item.title
                    target_lesson_description = target_item.description
                    
                    # DEBUG LOG
                    self.logger.info(f"🎯 [LESSON {index}] Using roadmap item:")
                    self.logger.info(f"   Index: {roadmap_index} (lesson {index})")
                    self.logger.info(f"   Title: {target_lesson_title}")
                    self.logger.info(f"   Description: {target_lesson_description}")
                 except Exception as e:
                    self.logger.error(f"Failed to extract roadmap item {roadmap_index}: {e}")
                    slim_roadmap = state.roadmap[:1]
            else:
                 # Fallback if index out of range
                 self.logger.warning(f"Index {index} out of range for roadmap (len={len(state.roadmap)})")
                 slim_roadmap = state.roadmap[:1]
        
        # PROGRESSIVE RETRIEVAL: Execute 3-layer retrieval BEFORE LLM
        from agents.base.progressive_retrieval import execute_progressive_retrieval
        
        # Use lesson description as seed (planner's outline) for query building
        lesson_context = f"{target_lesson_title}. {target_lesson_description}" if target_lesson_description else target_lesson_title
        
        self.logger.info(f"🔍 [LESSON {index}] Retrieval seed: '{lesson_context}' (title='{target_lesson_title}', desc='{target_lesson_description}')")
        
        tracer.record("retrieval", f"starting progressive 3-layer retrieval for lesson {index}")
        
        # Create retrieval function wrapper
        def retrieval_func(query: str, material_id: str, k: int = 5):
            tool = self.tools.get("retrieval_tool")
            if not tool:
                raise ValueError("retrieval_tool not found!")
            result = tool._run(id=material_id, query=query, k=k)
            return result
        
        # Execute progressive retrieval with LESSON DESCRIPTION (planner's seed) as context
        retrieval_results = execute_progressive_retrieval(
            retrieval_tool_func=retrieval_func,
            material_id=state.id,
            context_title=lesson_context,  # SEED from planner: title + description
            k=5
        )
        
        self.logger.info(f"[LESSON {index}] Progressive retrieval: L1={retrieval_results['layer1_query'][:30]}... | L2={retrieval_results['layer2_query'][:30]}... | L3={retrieval_results['layer3_query'][:30]}...")
        tracer.record("retrieval", f"completed 3 layers for lesson {index}",
                     layer1_query=retrieval_results['layer1_query'],
                     layer2_query=retrieval_results['layer2_query'],
                     layer3_query=retrieval_results['layer3_query'])
        
        # CoT: Build context and instruction messages
        base_instruction = self.prompt_manager.get_prompt(self.name).format(
            id=state.id,
            history=[],
            difficulty=state.difficulty,
            duration=str(state.duration),
            title=target_lesson_title,
            description=state.description,
            roadmap=slim_roadmap or state.roadmap,
            lessons_expected=state.lessons_expected or "",
            next_lesson_index=str(index),
            prev_lessons=prev_lessons,
        )
        
        context_msg = SystemMessage(content=f"""
⚠️ RETRIEVED CONTEXT FOR LESSON {index} ⚠️

Topic: {target_lesson_title}
Description: {target_lesson_description}

{retrieval_results['all_text']}

Use ONLY this context to create the lesson content.
""")
        
        task_msg = SystemMessage(content=base_instruction + "\n\nAnalyze the retrieved context and create lesson content following the step-by-step reasoning process.")
        history: List = [context_msg, task_msg]
        
        # CoT: Use structured output instead of free-form JSON
        from langchain_openai import ChatOpenAI
        from constant import LLM_MAX_TOKENS_LESSON, LLM_REQUEST_TIMEOUT, LLM_TEMPERATURE
        from schemas.context import LessonAnalysis
        
        cot_llm = ChatOpenAI(
            model_name=self.foundation_model,
            openai_api_key=self.llm.openai_api_key,
            temperature=LLM_TEMPERATURE,
            request_timeout=LLM_REQUEST_TIMEOUT,
            max_tokens=LLM_MAX_TOKENS_LESSON
        )
        structured_llm = cot_llm.with_structured_output(LessonAnalysis)
        
        analysis: LessonAnalysis = structured_llm.invoke(history)
        
        # Log CoT reasoning (minimal)
        self.logger.info(f"[LESSON {index} CoT] Topic: {analysis.lesson_topic}")
        self.logger.info(f"[LESSON {index} CoT] Key points: {', '.join(analysis.key_points)}")
        tracer.record("cot_lesson", "reasoning completed", index=index,
                     topic=analysis.lesson_topic,
                     points_count=len(analysis.key_points))
        tracer.record("llm", "CoT structured output", index=index, 
                     title=analysis.lesson_title[:50] if analysis.lesson_title else "(no title)",
                     content_length=len(analysis.lesson_content) if analysis.lesson_content else 0)
        
        # Validate structured output
        if not analysis.lesson_title or not analysis.lesson_content:
            tracer.record("error", "incomplete CoT output", index=index,
                         has_title=bool(analysis.lesson_title),
                         has_content=bool(analysis.lesson_content))
            raise ValueError(
                f"Lesson {index}: Incomplete CoT output - "
                f"title={bool(analysis.lesson_title)}, content={bool(analysis.lesson_content)}"
            )
        
        # Return the structured output
        # Convert to Lesson object
        lesson_id = f"{state.id}-L{index}"
        lesson = Lesson(
            lesson_id=lesson_id,
            title=analysis.lesson_title,
            overview="Bài học này sẽ giúp bạn hiểu rõ về chủ đề.",
            content=analysis.lesson_content,
            duration=30,
            assessments=None
        )

        tracer.record("done", "single lesson generated", index=index, lesson_id=lesson.lesson_id, 
                     content_length=len(analysis.lesson_content))
        
        return lesson

