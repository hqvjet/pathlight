from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END

from schemas.context import State
from agents.planner.planner_agent import PlannerAgent
from agents.lesson_creator.lesson_creator_agent import LessonCreatorAgent
from agents.test_creator.test_creator_agent import TestCreatorAgent
from agents.final_test_creator.final_test_creator_agent import FinalTestCreatorAgent
from agents.orchestrator.orchestrator import Orchestrator
from agents.base.prompt_manager import PromptManager
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
from utils import save_architecture
from config import config
from constant import (
    PLANNER_AGENT_NAME, 
    LESSON_CREATOR_AGENT_NAME, 
    TEST_CREATOR_AGENT_NAME, 
    FINAL_TEST_CREATOR_AGENT_NAME, 
    ORCHESTRATOR_AGENT_NAME
)

class CourseAgentFactory:
    def __init__(self):
        self.graph = StateGraph(State)
        prompt_manager = PromptManager()
        llm_manager = LLMManager()
        tool_manager = ToolManager()
        
        self.orchestrator = Orchestrator()
        self.planner_agent = PlannerAgent(
            name=PLANNER_AGENT_NAME, 
            foundation_model="gpt-5-nano", 
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager
        )
        self.lesson_creator_agent = LessonCreatorAgent(
            name=LESSON_CREATOR_AGENT_NAME,
            foundation_model="gpt-5-nano",
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager
        )
        self.test_creator_agent = TestCreatorAgent(
            name=TEST_CREATOR_AGENT_NAME,
            foundation_model="gpt-5-nano",
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager
        )
        self.final_test_creator_agent = FinalTestCreatorAgent(
            name=FINAL_TEST_CREATOR_AGENT_NAME,
            foundation_model="gpt-5-nano",
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager,
        )
        self.build_graph()

    def build_nodes(self):
        # Register all nodes with proper callables
        self.graph.add_node("orchestrator", lambda state: state)
        self.graph.add_node("planner", self.planner_agent)
        self.graph.add_node("lesson_creator", self.lesson_creator_agent)
        self.graph.add_node("test_creator", self.test_creator_agent)
        self.graph.add_node("final_test_creator", self.final_test_creator_agent)

    def build_edges(self):
        self.graph.add_edge(START, 'orchestrator')
        self.graph.add_conditional_edges(
            'orchestrator',
            path=self.orchestrator,
            path_map={
                'create_plan': 'planner',
                'create_lesson': 'lesson_creator',
                'create_test': 'test_creator',
                'create_final_test': 'final_test_creator',
                'done': END,
            },
        )
        self.graph.add_edge('planner', 'orchestrator')
        self.graph.add_edge('lesson_creator', 'orchestrator')
        self.graph.add_edge('test_creator', 'orchestrator')
        self.graph.add_edge('final_test_creator', 'orchestrator')

    def build_graph(self):
        self.build_nodes()
        self.build_edges()

graph = CourseAgentFactory().graph
course_agent = graph.compile()
# save_architecture(course_agent, filename="course_architecture.png")

async def invoke_course_agent(payload):
    # Increase recursion limit to avoid GraphRecursionError for complex routes
    results = await course_agent.ainvoke(payload, recursion_limit=getattr(config, "RECURSION_LIMIT", 500))
    return results



# Quick manual test (optional). Run this module directly to test.
if __name__ == "__main__":
    import asyncio
    async def _test():
        init_state: State = State(id="485935532", difficulty="medium", duration=1200)
        result = await invoke_course_agent(init_state)
        # Print a concise summary instead of the full object
        lessons = getattr(result, "lessons", []) or []
        print(
            "Final result | "+
            f"title={getattr(result, 'title', None)} | "
            f"roadmap_len={len(getattr(result, 'roadmap', []) or [])} | "
            f"lessons={len(lessons)}"
        )
    asyncio.run(_test())