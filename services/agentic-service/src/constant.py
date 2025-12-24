PLANNER_AGENT_NAME = "planner_agent"
LESSON_CREATOR_AGENT_NAME = "lesson_creator_agent"
TEST_CREATOR_AGENT_NAME = "test_creator_agent"
FINAL_TEST_CREATOR_AGENT_NAME = "final_test_creator_agent"
ORCHESTRATOR_AGENT_NAME = "orchestrator_agent"

# Iteration limits
MAX_TOOL_CALLS_PER_AGENT = 15  # Hard limit per agent invocation
MAX_GRAPH_ITERATIONS = 25  # Max total workflow iterations
EARLY_STOP_NO_PROGRESS_LIMIT = 3  # Stop if no state change for N iterations