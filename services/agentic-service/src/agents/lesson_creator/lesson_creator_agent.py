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
                    current_lesson_title = state.roadmap[roadmap_idx].get("title", "")
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
                status.mark_lessons_progress(state.id, len(lessons), planned_total)
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
            status.mark_lessons_progress(state.id, len(lessons), planned)
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
        """Generate one lesson for the given index, with tool-call loop and robust JSON parsing."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)

        # Keep roadmap minimal: only the current item to reduce tokens
        # CRITICAL: Pass the specific title of the lesson to be generated
        target_lesson_title = f"Lesson {index}"
        slim_roadmap = None
        if state.roadmap:
            # Try to get the specific roadmap item for this lesson
            roadmap_index = index - 1
            if 0 <= roadmap_index < len(state.roadmap):
                 try:
                    target_item = state.roadmap[roadmap_index]
                    slim_roadmap = [target_item]
                    target_lesson_title = target_item.get("title", target_lesson_title)
                 except:
                    slim_roadmap = state.roadmap[:1]
            else:
                 # Fallback if index out of range
                 slim_roadmap = state.roadmap[:1]

        history: List = [
            SystemMessage(
                content=self.prompt_manager.get_prompt(self.name).format(
                    id=state.id,
                    history=[],
                    difficulty=state.difficulty,
                    duration=str(state.duration),
                    title=target_lesson_title, # Pass SPECIFIC lesson title, not course title
                    description=state.description,
                    roadmap=slim_roadmap or state.roadmap,
                    lessons_expected=state.lessons_expected or "",
                    next_lesson_index=str(index),
                    prev_lessons=prev_lessons,
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
                "roadmap": slim_roadmap or state.roadmap,
                "lessons_expected": state.lessons_expected or "",
                "next_lesson_index": str(index),
                "prev_lessons": prev_lessons,
            }
        )
        # CRITICAL FIX: Append initial AI message to history
        history.append(ai)
        tracer.record("llm", "initial response", index=index, content_preview=str(ai.content)[:200])

        count = 1
        previous_queries = []  # Track queries for loop detection
        query_keywords_seen = set()  # Track keywords across all queries
        
        def normalize_query_for_comparison(q: str) -> str:
            """Normalize query for comparison."""
            return " ".join(sorted(set(q.lower().split())))
        
        def get_query_keywords(q: str) -> set:
            """Extract keywords from query."""
            stopwords = {'the', 'a', 'an', 'is', 'are', 'of', 'to', 'for', 'and', 'or', 'in', 'on', 'at', 'về', 'của', 'và', 'là'}
            return set(q.lower().split()) - stopwords
        
        while getattr(ai, "tool_calls", None) and count <= MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("tools", "llm requested tools", index=index, tool_calls=ai.tool_calls, iteration=count)
            
            # CRITICAL: Smart loop detection - check BEFORE executing tools
            current_queries = [tc.get("args", {}).get("query", "") for tc in ai.tool_calls]
            is_repetition = False
            
            for cq in current_queries:
                cq_normalized = normalize_query_for_comparison(cq)
                cq_keywords = get_query_keywords(cq)
                
                # Check exact match or high keyword overlap
                for prev in previous_queries:
                    if normalize_query_for_comparison(prev) == cq_normalized:
                        is_repetition = True
                        break
                
                if not is_repetition and query_keywords_seen:
                    overlap = len(cq_keywords & query_keywords_seen) / len(cq_keywords) if cq_keywords else 0
                    if overlap > 0.7:
                        is_repetition = True
                
                query_keywords_seen.update(cq_keywords)
            
            if is_repetition:
                self.logger.warning(f"Lesson Creator detected repeated query at iteration {count}, forcing output")
                tracer.record("warn", "query repetition detected - forcing output", index=index, iteration=count)
                break  # Exit immediately to force JSON output
            
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
                
                # CRITICAL: Inject strong guidance for weak LLM
                remaining = MAX_TOOL_CALLS_PER_AGENT - count
                queries_str = ", ".join([f'"{q[:30]}..."' for q in previous_queries[-2:]]) if previous_queries else "(chưa có)"
                
                guidance = SystemMessage(content=(
                    f"\n=== TRẠNG THÁI ==="
                    f"\n• Lượt retrieval: {count}/{MAX_TOOL_CALLS_PER_AGENT} (còn {remaining})"
                    f"\n• Query đã gọi: {queries_str}"
                    f"\n\n=== HÀNH ĐỘNG ==="
                    f"\n• Nếu có nội dung về '{target_lesson_title}' → VIẾT BÀI NGAY"
                    f"\n• KHÔNG gọi lại query tương tự"
                    f"\n• Còn {remaining} lượt → sau đó BẮT BUỘC output JSON"
                ))
                history.append(guidance)
                
                # Token optimization: Trim history to prevent explosion
                history = trim_history(history)
                tracer.record(
                    "tool_result",
                    f"{tool_name} executed",
                    index=index,
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
                        "roadmap": slim_roadmap or state.roadmap,
                        "lessons_expected": state.lessons_expected or "",
                        "next_lesson_index": str(index),
                        "prev_lessons": prev_lessons,
                    }
                )
            # CRITICAL FIX: Append the new AI message to history for the NEXT iteration
            history.append(ai)
            count += 1

        # CRITICAL FIX: Force final JSON output after hitting max tool calls
        if getattr(ai, "tool_calls", None):
            tracer.record(
                "warn",
                "tool budget exhausted; forcing final JSON output",
                index=index,
                rounds=count - 1,
                max_rounds=MAX_TOOL_CALLS_PER_AGENT,
            )
            self.logger.warning(f"Lesson Creator hit max tool calls: {MAX_TOOL_CALLS_PER_AGENT}")
            # CRITICAL: Create LLM WITHOUT tools binding to prevent further tool calls
            from langchain_openai import ChatOpenAI
            from constant import LLM_MAX_TOKENS_LESSON, LLM_REQUEST_TIMEOUT, LLM_TEMPERATURE
            final_llm = ChatOpenAI(
                model_name=self.foundation_model,
                openai_api_key=self.llm.openai_api_key,
                temperature=LLM_TEMPERATURE,  # CRITICAL: 0 for deterministic output
                request_timeout=LLM_REQUEST_TIMEOUT,
                max_tokens=LLM_MAX_TOKENS_LESSON,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
            final_chain = self.build_chain(final_llm)
            
            try:
                ai = final_chain.invoke(
                    {
                        "id": state.id,
                        "history": history,
                        "difficulty": state.difficulty,
                        "duration": str(state.duration),
                        "title": state.title,
                        "description": state.description,
                        "roadmap": slim_roadmap or state.roadmap,
                        "lessons_expected": state.lessons_expected or "",
                        "next_lesson_index": str(index),
                        "prev_lessons": prev_lessons,
                    }
                )
            except Exception as e:
                # Handle LengthFinishReasonError
                if "LengthFinishReasonError" in str(type(e).__name__) or "length limit" in str(e).lower():
                    tracer.record("error", "hit token limit even after forcing short output", index=index, error=str(e))
                    raise ValueError(
                        f"Lesson {index}: LLM exceeded token limit even with shortened instructions. "
                        "Try reducing content requirements further or increasing max_tokens."
                    )
                raise

        # CRITICAL FIX: Validate content before parsing
        if not ai.content or not ai.content.strip():
            tracer.record("error", "empty content", index=index, has_tool_calls=bool(getattr(ai, 'tool_calls', None)))
            raise ValueError(
                f"Lesson {index}: LLM returned empty content. "
                f"Has tool_calls: {bool(getattr(ai, 'tool_calls', None))}"
            )
        
        # Log content for debugging
        self.logger.debug(f"Lesson {index} LLM content (first 1000 chars): {ai.content[:1000]}")
        
        # Parse JSON robustly and build a single Lesson
        try:
            json_content = json.loads(ai.content)
        except Exception as e:
            tracer.record("error", "failed to parse ai json", index=index, error=str(e), content=ai.content[:500])
            self.logger.error(f"Lesson {index} JSON parse error. Content: {ai.content[:1000]}")
            raise ValueError(f"Lesson {index}: Failed to parse LLM JSON response - {str(e)}")

        # CRITICAL FIX: Strict JSON structure validation
        lessons_array = json_content.get("lessons")
        if not lessons_array:
            tracer.record("error", "no 'lessons' field in response", index=index, keys=list(json_content.keys()))
            raise ValueError(f"Lesson {index}: LLM response missing 'lessons' field. Got keys: {list(json_content.keys())}")
        
        if not isinstance(lessons_array, list) or len(lessons_array) == 0:
            tracer.record("error", "lessons field is not a non-empty list", index=index, type=type(lessons_array))
            raise ValueError(f"Lesson {index}: 'lessons' must be non-empty list, got {type(lessons_array)}")

        obj = lessons_array[0]
        
        # CRITICAL FIX: Strict field validation
        lesson_id = obj.get("lesson_id") or f"{state.id}-L{index}"
        title = obj.get("title")
        if not title:
            tracer.record("error", "missing title", index=index)
            raise ValueError(f"Lesson {index}: missing required field 'title'")
        
        overview = obj.get("overview") or "Bài học này sẽ giúp bạn hiểu rõ về chủ đề."
        
        content = obj.get("content") or ""
        from constant import MIN_CONTENT_LENGTH
        if not content or len(content.strip()) < MIN_CONTENT_LENGTH:
            tracer.record("warn", "content shorter than recommended", index=index, length=len(content) if content else 0, min=MIN_CONTENT_LENGTH)
        
        # Truncate if too long (safety)
        from constant import MAX_CONTENT_LENGTH
        if len(content) > MAX_CONTENT_LENGTH:
            tracer.record("warn", "content truncated", index=index, original_len=len(content), max=MAX_CONTENT_LENGTH)
            content = content[:MAX_CONTENT_LENGTH]
        
        duration = obj.get("duration") or 30
        
        # Parse assessments with strict validation
        assessments_raw = obj.get("assessments") or []
        assessments = []
        for qa_idx, qa in enumerate(assessments_raw):
            try:
                # CRITICAL FIX: Validate answer format
                answer = qa.get("answer")
                if isinstance(answer, str):
                    # Try to extract number from string like "1", "A", "option 1"
                    import re
                    match = re.search(r'\d+', str(answer))
                    if match:
                        answer = int(match.group())
                    else:
                        # If no number found, try to map A/B/C/D to 1/2/3/4
                        answer_upper = answer.strip().upper()
                        if answer_upper in ['A', 'B', 'C', 'D']:
                            answer = ord(answer_upper) - ord('A') + 1
                        else:
                            tracer.record("warn", f"assessment {qa_idx}: invalid answer format", answer=answer)
                            continue  # Skip invalid assessment
                elif not isinstance(answer, int):
                    tracer.record("warn", f"assessment {qa_idx}: answer not int or string", type=type(answer))
                    continue
                
                # Validate answer range
                if not (1 <= answer <= 4):
                    tracer.record("warn", f"assessment {qa_idx}: answer out of range", answer=answer)
                    continue
                
                # Validate options
                options = qa.get("options", [])
                if not isinstance(options, list) or len(options) != 4:
                    tracer.record("warn", f"assessment {qa_idx}: invalid options", count=len(options) if isinstance(options, list) else "not list")
                    continue
                
                assessments.append({
                    "question": qa.get("question", ""),
                    "options": options,
                    "answer": answer,
                    "hint": qa.get("hint", ""),
                    "explanation": qa.get("explanation", ""),
                    "difficulty": qa.get("difficulty", "medium")
                })
            except Exception as e:
                tracer.record("warn", f"assessment {qa_idx}: parse error", error=str(e))
                continue
        
        # Log warning if not exactly 3 assessments but don't reject
        from constant import MIN_ASSESSMENTS_COUNT
        if len(assessments) != MIN_ASSESSMENTS_COUNT:
            tracer.record("warn", "assessment count not ideal", index=index, valid=len(assessments), recommended=MIN_ASSESSMENTS_COUNT)
        
        lesson = Lesson(
            lesson_id=lesson_id,
            title=title,
            overview=overview,
            content=content,
            duration=duration,
            assessments=assessments if assessments else None
        )

        tracer.record("done", "single lesson generated", index=index, lesson_id=lesson.lesson_id, 
                     content_length=len(content), assessments_count=len(assessments))
        
        return lesson
