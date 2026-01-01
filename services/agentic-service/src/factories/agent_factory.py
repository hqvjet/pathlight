from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END

from schemas.context import State
from agents.planner.planner_agent import PlannerAgent
from agents.lesson_creator.lesson_creator_agent import LessonCreatorAgent
from agents.test_creator.test_creator_agent import TestCreatorAgent
from agents.orchestrator.orchestrator import Orchestrator
from agents.base.prompt_manager import PromptManager
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
# from utils import save_architecture  # Not needed in Lambda
from config import config
from constant import (
    PLANNER_AGENT_NAME, 
    LESSON_CREATOR_AGENT_NAME, 
    TEST_CREATOR_AGENT_NAME, 
    ORCHESTRATOR_AGENT_NAME,
    MAX_GRAPH_ITERATIONS
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
            foundation_model="gpt-4o-mini", 
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager
        )
        self.lesson_creator_agent = LessonCreatorAgent(
            name=LESSON_CREATOR_AGENT_NAME,
            foundation_model="gpt-4o-mini",
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager
        )
        self.test_creator_agent = TestCreatorAgent(
            name=TEST_CREATOR_AGENT_NAME,
            foundation_model="gpt-4o-mini",
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager
        )
        self.build_graph()

    def build_nodes(self):
        # Register all nodes with proper callables
        self.graph.add_node("orchestrator", lambda state: state)
        self.graph.add_node("planner", self.planner_agent)
        self.graph.add_node("lesson_creator", self.lesson_creator_agent)
        self.graph.add_node("test_creator", self.test_creator_agent)

    def build_edges(self):
        self.graph.add_edge(START, 'orchestrator')
        self.graph.add_conditional_edges(
            'orchestrator',
            path=self.orchestrator,
            path_map={
                'create_plan': 'planner',
                'create_lesson': 'lesson_creator',
                'create_test': 'test_creator',
                'done': END,
            },
        )
        self.graph.add_edge('planner', 'orchestrator')
        self.graph.add_edge('lesson_creator', 'orchestrator')
        self.graph.add_edge('test_creator', 'orchestrator')

    def build_graph(self):
        self.build_nodes()
        self.build_edges()

graph = CourseAgentFactory().graph
course_agent = graph.compile()
# save_architecture(course_agent, filename="course_architecture.png")

def invoke_course_agent(payload):
    """Invoke course agent synchronously with iteration limit."""
    recursion_limit = getattr(config, "RECURSION_LIMIT", 500)
    # Use the smaller of MAX_GRAPH_ITERATIONS or recursion_limit to prevent infinite loops
    max_iter = min(MAX_GRAPH_ITERATIONS, recursion_limit)
    results = course_agent.invoke(
        payload, 
        config={
            "recursion_limit": max_iter,
            "max_iterations": max_iter
        }
    )
    return results


# Quick manual test (optional). Run this module directly to test.
if __name__ == "__main__":
    init_state: State = State(id="test-001", difficulty="medium", duration=1200)
    result = invoke_course_agent(init_state)
    lessons = getattr(result, "lessons", []) or []
    print(
        "Final result | "+
        f"title={getattr(result, 'title', None)} | "
        f"roadmap_len={len(getattr(result, 'roadmap', []) or [])} | "
        f"lessons={len(lessons)}"
    )