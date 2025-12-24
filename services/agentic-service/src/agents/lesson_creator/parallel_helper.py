"""
Helper for parallel lesson generation using ThreadPoolExecutor for TRUE parallelism
"""
import asyncio
from typing import List, Optional
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

from schemas.context import State, Lesson
from core.tracing import StepTracer
from constant import MAX_TOOL_CALLS_PER_AGENT


def trim_history(history: List, max_messages: int = 10) -> List:
    """Keep only recent messages."""
    if len(history) <= max_messages:
        return history
    system_msg = history[0] if history and isinstance(history[0], SystemMessage) else None
    recent = history[-max_messages:]
    if system_msg and recent[0] != system_msg:
        return [system_msg] + recent
    return recent


async def generate_single_lesson_async(agent, state: State, index: int, prev_lessons: List[str]) -> Optional[Lesson]:
    """
    Async version for generating a single lesson in parallel.
    
    Args:
        agent: The LessonCreatorAgent instance
        state: Current state
        index: Lesson index (1-based)
        prev_lessons: List of previous lesson IDs
    
    Returns:
        Lesson object or None if failed
    """
    tracer = StepTracer(agent.name, state.id, logger=agent.logger)
    
    # Keep roadmap minimal
    slim_roadmap = None
    if state.roadmap and len(state.roadmap) >= index:
        try:
            slim_roadmap = [state.roadmap[index - 1]]
        except Exception:
            slim_roadmap = state.roadmap[:1]
    
    history: List = [
        SystemMessage(
            content=agent.prompt_manager.get_prompt(agent.name).format(
                id=state.id,
                history=[],
                difficulty=state.difficulty,
                duration=str(state.duration),
                title=state.title,
                description=state.description,
                roadmap=slim_roadmap or state.roadmap,
                lessons_expected=state.lessons_expected or "",
                next_lesson_index=str(index),
                prev_lessons=prev_lessons,
            )
        )
    ]
    
    # Use async invoke
    ai: AIMessage = await agent.chain.ainvoke(
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
    tracer.record("llm", f"lesson {index} initial", content_preview=str(ai.content)[:100])
    
    iteration = 1
    while getattr(ai, "tool_calls", None) and iteration <= MAX_TOOL_CALLS_PER_AGENT:
        tracer.record("tools", f"lesson {index} iteration {iteration}", count=len(ai.tool_calls))
        
        for tool_call in ai.tool_calls:
            tool_name = tool_call["name"]
            tool_call_id = tool_call["id"]
            args = tool_call["args"]
            
            if tool_name not in agent.tools:
                raise ValueError(f"Tool {tool_name} not found")
            
            # Execute tool - use sync wrapper since tool_manager might not be async
            result = agent.tool_manager.execute_tool_sync(tool_name, args)
            
            history.append(
                ToolMessage(tool_call_id=tool_call_id, name=tool_name, content=result)
            )
            history = trim_history(history)
        
        ai = await agent.chain.ainvoke(
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
        iteration += 1
    
    if getattr(ai, "tool_calls", None):
        tracer.record("warn", f"lesson {index} tool budget exhausted")
        history.append(SystemMessage(content="Ngừng gọi công cụ. Xuất JSON cuối cùng."))
        ai = await agent.chain.ainvoke(
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
    
    # Parse lesson
    try:
        json_content = json.loads(ai.content)
    except Exception as e:
        tracer.record("error", f"lesson {index} parse failed", error=str(e))
        return None
    
    obj = json_content.get("lesson") or json_content
    lesson_id = obj.get("lesson_id") or f"{state.id}-L{index}"
    title = obj.get("title") or obj.get("lesson_name") or f"Lesson {index}"
    overview = obj.get("overview") or obj.get("lesson_description") or ""
    content = obj.get("content") or obj.get("lesson_content") or ""
    duration = obj.get("duration") or 30
    
    # Parse assessments
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
        except Exception:
            continue
    
    lesson = Lesson(
        lesson_id=lesson_id,
        title=title,
        overview=overview,
        content=content,
        duration=duration,
        assessments=assessments if assessments else None
    )
    
    tracer.record("done", f"lesson {index} complete", lesson_id=lesson.lesson_id)
    return lesson


def generate_lessons_parallel(agent, state: State, count: int) -> Optional[List[Lesson]]:
    """
    Generate multiple lessons in TRUE PARALLEL using ThreadPoolExecutor.
    Each lesson runs in its own thread, making independent LLM calls.
    """
    tracer = StepTracer(agent.name, state.id, logger=agent.logger)
    tracer.record("start", "TRUE parallel lesson generation with threads", count=count)
    
    def generate_one_lesson_sync(index: int) -> tuple:
        """Wrapper to run async lesson generation in sync context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                generate_single_lesson_async(agent, state, index, [])
            )
            return (index, result, None)
        except Exception as e:
            return (index, None, e)
        finally:
            loop.close()
    
    # Use ThreadPoolExecutor for TRUE parallelism (multiple threads)
    lessons_dict = {}
    errors = {}
    
    with ThreadPoolExecutor(max_workers=min(count, 6)) as executor:  # Max 6 parallel to avoid rate limits
        # Submit all tasks
        futures = {
            executor.submit(generate_one_lesson_sync, i + 1): i + 1
            for i in range(count)
        }
        
        tracer.record("parallel", f"launched {count} threads (max_workers=6)")
        
        # Collect results as they complete
        for future in as_completed(futures):
            index, result, error = future.result()
            
            if error:
                tracer.record("error", f"lesson {index} failed", error=str(error))
                errors[index] = error
            elif result:
                lessons_dict[index] = result
                tracer.record("progress", f"lesson {index} completed", 
                            done=len(lessons_dict), total=count)
            else:
                tracer.record("warn", f"lesson {index} returned None")
    
    # Build ordered list with placeholders for failed lessons
    lessons = []
    for i in range(1, count + 1):
        if i in lessons_dict:
            lessons.append(lessons_dict[i])
        else:
            tracer.record("placeholder", f"lesson {i} using placeholder")
            lessons.append(Lesson(
                lesson_id=f"{state.id}-L{i}",
                title=f"Lesson {i}",
                overview="",
                content="",
                duration=30
            ))
    
    tracer.record("done", "parallel generation complete", 
                 success=len(lessons_dict), 
                 failed=len(errors),
                 total=count)
    return lessons