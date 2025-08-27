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


class LessonCreatorAgent(BaseAgent):
    def __init__(
        self, name: str, 
        foundation_model: str, 
        prompt_manager: PromptManager,
        llm_manager: LLMManager,
        tool_manager: ToolManager
    ):
        """
        Initialize the PlannerAgent.
        """
        super().__init__(name, foundation_model, prompt_manager)
        # Keep references to tools and llm so we can execute tool calls in a loop
        self.tool_manager = tool_manager
        self.tools = {t.name: t for t in tool_manager.get_tools(name)}
        self.llm = llm_manager.get_llm(model_name=foundation_model, tools=list(self.tools.values()))
        self.chain = self.build_chain(self.llm)

    async def __call__(self, state: State) -> State:
        print(f"[Lesson Agent] Invoked with state: {state}")
        history: List = [
            SystemMessage(content=self.prompt_manager.get_prompt(self.name).format(
                id=state.id, history=[], 
                difficulty=state.difficulty, 
                duration=str(state.duration),
                title=state.title,
                description=state.description,
                roadmap=state.roadmap
            ))
        ]

        ai: AIMessage = await self.chain.ainvoke(
            {
                "id": state.id, 
                "history": history, 
                "difficulty": state.difficulty, 
                "duration": str(state.duration),
                "title": state.title,
                "description": state.description,
                "roadmap": state.roadmap
            }
        )
        print(f"[Lesson Creator Agent] - AI Response FIRST: {ai}")
        history.append(ai)
        
        count = 1
        while ai.tool_calls:
            print(f"        Tool call {ai.tool_calls} detected. Type: {type(ai.tool_calls)}")
            for tool_call in ai.tool_calls:
                tool_name = tool_call['name']
                tool_call_id = tool_call['id']
                args = tool_call['args']
                print(f"        Executing tool {tool_name} with arguments {args}")
                if tool_name not in self.tools:
                    raise ValueError(f"Tool {tool_name} not found in tools.")

                result = await self.tool_manager.execute_tool(tool_name, args)
                history.append(ToolMessage(tool_call_id=tool_call_id, name=tool_name, content=result))

                ai = await self.chain.ainvoke(
                    {
                        "id": state.id, 
                        "history": history, 
                        "difficulty": state.difficulty, 
                        "duration": str(state.duration),
                        "title": state.title,
                        "description": state.description,
                        "roadmap": state.roadmap
                    }
                )
                count += 1
                print(f"[Lesson Creator Agent] - Response {count}: {ai}")

        json_content = json.loads(ai.content)
        # state.title = json_content.get('course_name')
        # state.description = json_content.get('course_description')
        # state.roadmap = json_content.get('course_roadmap')
        print(f"[Lesson Creator Agent] - Final response: {json_content}")
        state.lessons = json_content.get('lessons', [])

        return state