from dotenv import load_dotenv
load_dotenv()

from typing import List
import json
from agents.base.base_agent import BaseAgent
from agents.base.prompt_manager import PromptManager
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

from schemas.context import QuizState, QuizCard
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


class QuestionerAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        foundation_model: str,
        prompt_manager: PromptManager,
        llm_manager: LLMManager,
        tool_manager: ToolManager,
    ):
        """Initialize the QuestionerAgent."""
        super().__init__(name, foundation_model, prompt_manager)
        self.tool_manager = tool_manager
        self.tools = {t.name: t for t in tool_manager.get_tools(name)}
        
        from constant import LLM_MAX_TOKENS_QUESTIONER
        self.llm = llm_manager.get_llm(
            model_name=foundation_model,
            tools=list(self.tools.values()),
            max_tokens=LLM_MAX_TOKENS_QUESTIONER,
            enable_json_mode=True
        )
        self.chain = self.build_chain(self.llm)
        self.logger = setup_logger(__name__)

    def __call__(self, state: QuizState) -> QuizState:
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        tracer.record("start", "invoke questioner", difficulty=state.difficulty, num_questions=state.num_questions)

        quiz_cards = state.quiz_cards or []
        if state.quiz_cards is None:
            state.quiz_cards = quiz_cards

        ideas = state.ideas or []
        if not ideas:
            self.logger.warning("No ideas from planner - cannot generate questions")
            return state

        # Sequential generation: one question at a time
        next_index = state.next_card_index or 0
        
        # Stop at num_questions, not len(ideas) - planner might generate more ideas than needed
        if next_index < state.num_questions and next_index < len(ideas):
            idea = ideas[next_index]
            tracer.record("single", "generate question from idea", index=next_index, topic=idea.topic)
            
            result = self._generate_single_question(state, idea, next_index + 1, [q.card_id for q in quiz_cards])
            if result is None:
                raise ValueError(f"Failed to generate question {next_index + 1}: LLM returned None or invalid JSON")
            
            quiz_cards.append(result)
            state.quiz_cards = quiz_cards  # Assign back to state
            state.next_card_index = next_index + 1
            tracer.record("done", "question appended", card_id=result.card_id, next_index=state.next_card_index)
            
        return state

    def _generate_single_question(self, state: QuizState, idea, question_number: int, prev_ids: List[str]) -> QuizCard:
        """Generate a single quiz question based on an idea."""
        tracer = StepTracer(self.name, state.id, logger=self.logger)
        
        # REUSE PLANNER'S GENERAL CONTEXT
        general_context = state.retrieved_context or ""
        
        # RETRIEVE SPECIFIC CONTEXT for this question idea (1 layer only)
        query = f"{idea.topic} {idea.description}" if idea.description else idea.topic
        tracer.record("retrieval", f"Retrieving specific context for question {question_number}", query=query[:50])
        
        try:
            tool = self.tools.get("retrieval_tool")
            if not tool:
                raise ValueError("retrieval_tool not found!")
            
            specific_context = tool._run(id=state.id, query=query, k=3)  # k=3 for focused context
            self.logger.info(f"[QUESTION {question_number}] Retrieved specific context: {len(specific_context)} chars for '{query[:40]}...'")
        except Exception as e:
            self.logger.warning(f"[QUESTION {question_number}] Failed to retrieve specific context: {e}")
            specific_context = ""
        
        # COMBINE: general context + specific context for this question
        if general_context and specific_context:
            retrieved_context = f"=== GENERAL CONTEXT ===\n{general_context}\n\n=== SPECIFIC CONTEXT FOR THIS QUESTION ===\n{specific_context}"
        elif general_context:
            retrieved_context = general_context
        elif specific_context:
            retrieved_context = specific_context
        else:
            self.logger.warning(f"[QUESTION {question_number}] No context available!")
            retrieved_context = ""
        
        tracer.record("context", f"Combined context ready", 
                     general_len=len(general_context), 
                     specific_len=len(specific_context),
                     total_len=len(retrieved_context))
        
        history: List = [
            SystemMessage(
                content=self.prompt_manager.get_prompt(self.name).format(
                    id=state.id,
                    history=[],
                    difficulty=state.difficulty,
                    duration=str(state.duration),
                    title=state.title or "",
                    overview=state.overview or "",
                    idea_topic=idea.topic,
                    idea_description=idea.description,
                    idea_difficulty=idea.difficulty,
                    question_number=question_number,
                    prev_card_ids=prev_ids,
                    retrieved_context=retrieved_context,
                )
            )
        ]

        ai: AIMessage = self.chain.invoke(
            {
                "id": state.id,
                "history": history,
                "difficulty": state.difficulty,
                "duration": str(state.duration),
                "title": state.title or "",
                "overview": state.overview or "",
                "idea_topic": idea.topic,
                "idea_description": idea.description,
                "idea_difficulty": idea.difficulty,
                "question_number": question_number,
                "prev_card_ids": prev_ids,
                "retrieved_context": retrieved_context,
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
                history = trim_history(history)
                tracer.record("tool_result", f"{tool_name} executed", args=args, result_preview=str(result)[:200])

                ai = self.chain.invoke(
                    {
                        "id": state.id,
                        "history": history,
                        "difficulty": state.difficulty,
                        "duration": str(state.duration),
                        "title": state.title or "",
                        "overview": state.overview or "",
                        "idea_topic": idea.topic,
                        "idea_description": idea.description,
                        "idea_difficulty": idea.difficulty,
                        "question_number": question_number,
                        "prev_card_ids": prev_ids,
                        "retrieved_context": retrieved_context,
                    }
                )
            count += 1

        # Force final JSON output if max tool calls reached
        if count > MAX_TOOL_CALLS_PER_AGENT:
            tracer.record("warn", f"Hit max tool calls limit: {MAX_TOOL_CALLS_PER_AGENT}")
            self.logger.warning(f"Questioner hit max tool calls: {MAX_TOOL_CALLS_PER_AGENT}")
            
            from langchain_openai import ChatOpenAI
            from constant import LLM_MAX_TOKENS_QUESTIONER, LLM_REQUEST_TIMEOUT
            final_llm = ChatOpenAI(
                model_name=self.foundation_model,
                openai_api_key=self.llm.openai_api_key,
                temperature=0.3,
                request_timeout=LLM_REQUEST_TIMEOUT,
                max_tokens=LLM_MAX_TOKENS_QUESTIONER,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
            final_chain = self.build_chain(final_llm)
            
            try:
                ai = final_chain.invoke({
                    "id": state.id,
                    "history": history,
                    "difficulty": state.difficulty,
                    "duration": str(state.duration),
                    "title": state.title or "",
                    "overview": state.overview or "",
                    "idea_topic": idea.topic,
                    "idea_description": idea.description,
                    "idea_difficulty": idea.difficulty,
                    "question_number": question_number,
                    "prev_card_ids": prev_ids,
                    "retrieved_context": retrieved_context,
                })
            except Exception as e:
                tracer.record("error", "Final invoke failed", error=str(e))
                raise ValueError(f"Final invoke failed: {str(e)}")

        # Parse JSON response
        content = ai.content
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                tracer.record("error", "JSON parse failed", content=content[:500])
                raise ValueError(f"Failed to parse JSON: {str(e)}")
        elif isinstance(content, dict):
            data = content
        else:
            raise ValueError(f"Unexpected content type: {type(content)}")

        # Validate and create QuizCard
        try:
            card_id = f"{state.id}_card_{question_number}"
            quiz_card = QuizCard(
                card_id=card_id,
                question=data.get("question", ""),
                hint=data.get("hint", ""),
                explanation=data.get("explanation", ""),
                difficulty=data.get("difficulty", idea.difficulty),
                option1=data.get("option1", ""),
                option2=data.get("option2", ""),
                option3=data.get("option3", ""),
                option4=data.get("option4", ""),
                answer=data.get("answer", 1),
            )
            tracer.record("success", "QuizCard created", card_id=card_id)
            return quiz_card
        except Exception as e:
            tracer.record("error", "QuizCard validation failed", error=str(e), data=data)
            raise ValueError(f"Failed to create QuizCard: {str(e)}")
