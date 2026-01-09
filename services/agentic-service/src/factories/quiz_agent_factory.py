from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END

from schemas.context import QuizState
from agents.quiz_planner.quiz_planner_agent import QuizPlannerAgent
from agents.questioner.questioner_agent import QuestionerAgent
from agents.orchestrator.quiz_orchestrator import QuizOrchestrator
from agents.base.prompt_manager import PromptManager
from agents.base.llm_manager import LLMManager
from agents.base.tool_manager import ToolManager
from config import config
from constant import (
    MAX_GRAPH_ITERATIONS,
    QUIZ_PLANNER_AGENT_NAME,
    QUESTIONER_AGENT_NAME,
)


class QuizAgentFactory:
    def __init__(self):
        self.graph = StateGraph(QuizState)
        prompt_manager = PromptManager()
        llm_manager = LLMManager()
        tool_manager = ToolManager()
        
        self.orchestrator = QuizOrchestrator()
        # QUALITY: Use GPT-4o for quiz planner to generate better quiz structure
        self.quiz_planner_agent = QuizPlannerAgent(
            name=QUIZ_PLANNER_AGENT_NAME,
            foundation_model="gpt-4o",
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager
        )
        self.questioner_agent = QuestionerAgent(
            name=QUESTIONER_AGENT_NAME,
            foundation_model="gpt-4o-mini",
            prompt_manager=prompt_manager,
            llm_manager=llm_manager,
            tool_manager=tool_manager
        )
        self.build_graph()

    def build_nodes(self):
        # Register all nodes
        self.graph.add_node("orchestrator", lambda state: state)
        self.graph.add_node("quiz_planner", self.quiz_planner_agent)
        self.graph.add_node("questioner", self.questioner_agent)

    def build_edges(self):
        self.graph.add_edge(START, 'orchestrator')
        self.graph.add_conditional_edges(
            'orchestrator',
            path=self.orchestrator,
            path_map={
                'create_quiz_plan': 'quiz_planner',
                'create_quiz_question': 'questioner',
                'done': END,
            },
        )
        self.graph.add_edge('quiz_planner', 'orchestrator')
        self.graph.add_edge('questioner', 'orchestrator')

    def build_graph(self):
        self.build_nodes()
        self.build_edges()


quiz_graph = QuizAgentFactory().graph
quiz_agent = quiz_graph.compile()


def invoke_quiz_agent(payload: QuizState) -> QuizState:
    """Invoke quiz agent synchronously with iteration limit."""
    recursion_limit = getattr(config, "RECURSION_LIMIT", 500)
    max_iter = min(MAX_GRAPH_ITERATIONS, recursion_limit)
    results = quiz_agent.invoke(
        payload,
        config={
            "recursion_limit": max_iter,
            "max_iterations": max_iter
        }
    )
    return results


# Quick manual test
if __name__ == "__main__":
    init_state = QuizState(
        id="test-quiz-001",
        difficulty="medium",
        duration=600,
        num_questions=5
    )
    result = invoke_quiz_agent(init_state)
    quiz_cards = getattr(result, "quiz_cards", []) or []
    print(
        f"Final result | "
        f"title={getattr(result, 'title', None)} | "
        f"ideas={len(getattr(result, 'ideas', []) or [])} | "
        f"cards={len(quiz_cards)}"
    )
