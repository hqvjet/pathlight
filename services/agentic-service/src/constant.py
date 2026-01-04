PLANNER_AGENT_NAME = "planner_agent"
LESSON_CREATOR_AGENT_NAME = "lesson_creator_agent"
TEST_CREATOR_AGENT_NAME = "test_creator_agent"
FINAL_TEST_CREATOR_AGENT_NAME = "final_test_creator_agent"
ORCHESTRATOR_AGENT_NAME = "orchestrator_agent"

# Iteration limits - REDUCED to prevent timeout
MAX_TOOL_CALLS_PER_AGENT = 3  # CRITICAL: Giảm từ 15→3 để tránh token explosion
MAX_GRAPH_ITERATIONS = 50  # Tăng để đủ cho lessons (orchestrator iterations)
EARLY_STOP_NO_PROGRESS_LIMIT = 3  # Stop if no state change for N iterations

# Timeout settings
LLM_REQUEST_TIMEOUT = 180  # Timeout for each LLM request (seconds) - increased for long content generation
LESSON_GENERATION_TIMEOUT = 90  # Timeout for single lesson generation (seconds)

# LLM max_tokens settings per agent type
# CRITICAL: Must be tuned to prevent truncation while avoiding excessive tokens
LLM_MAX_TOKENS_PLANNER = None  # No limit - needs full roadmap JSON
LLM_MAX_TOKENS_LESSON = 8000   # Increased for extensive academic content (150-250 lines)
LLM_MAX_TOKENS_TEST = 1500     # 4-6 assessments

# LLM temperature settings
LLM_TEMPERATURE = 0.0  # CRITICAL: 0 for deterministic output (no randomness)

# Content validation
MIN_CONTENT_LENGTH = 800      # Minimum content chars (realistic for detailed lessons)
MAX_CONTENT_LENGTH = 8000     # Maximum content chars (for comprehensive, detailed lessons)
MIN_ASSESSMENTS_COUNT = 3     # CRITICAL: EXACTLY 3 assessments per lesson (not >=3)
MAX_ASSESSMENTS_COUNT = 3     # CRITICAL: EXACTLY 3 assessments per lesson (not <=3)
MIN_ROADMAP_ITEMS = 2         # Minimum roadmap items
MAX_ROADMAP_ITEMS = 10        # Maximum roadmap items (prevent too many lessons)