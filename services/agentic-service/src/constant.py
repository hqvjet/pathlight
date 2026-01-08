PLANNER_AGENT_NAME = "planner_agent"
LESSON_CREATOR_AGENT_NAME = "lesson_creator_agent"
TEST_CREATOR_AGENT_NAME = "test_creator_agent"
FINAL_TEST_CREATOR_AGENT_NAME = "final_test_creator_agent"
ORCHESTRATOR_AGENT_NAME = "orchestrator_agent"

# Quiz agent names
QUIZ_PLANNER_AGENT_NAME = "quiz_planner"
QUESTIONER_AGENT_NAME = "questioner"
QUIZ_ORCHESTRATOR_AGENT_NAME = "quiz_orchestrator"

# Iteration limits - STRICT for token optimization
MAX_TOOL_CALLS_PER_AGENT = 2  # CRITICAL: Chỉ cho phép TỐI ĐA 2 lượt retrieval - đủ cho scan + deep dive
MAX_GRAPH_ITERATIONS = 50  # Tăng để đủ cho lessons (orchestrator iterations)
EARLY_STOP_NO_PROGRESS_LIMIT = 3  # Stop if no state change for N iterations

# Timeout settings
LLM_REQUEST_TIMEOUT = 180  # Timeout for each LLM request (seconds) - increased for long content generation
LESSON_GENERATION_TIMEOUT = 90  # Timeout for single lesson generation (seconds)

# LLM max_tokens settings per agent type
# CRITICAL: Must be tuned to prevent truncation while avoiding excessive tokens
LLM_MAX_TOKENS_PLANNER = None  # No limit - needs full roadmap JSON
LLM_MAX_TOKENS_LESSON = None   # No limit - let LLM decide based on prompt guidance
LLM_MAX_TOKENS_TEST = 1500     # 4-6 assessments
LLM_MAX_TOKENS_QUESTIONER = 2000  # Quiz question generation

# LLM temperature settings
LLM_TEMPERATURE = 0.0  # CRITICAL: 0 for deterministic output (no randomness)

# Content validation - soft limits, không enforce strict
MIN_CONTENT_LENGTH = 300      # Soft minimum (chỉ warning, không reject)
MAX_CONTENT_LENGTH = 10000    # Soft maximum (chỉ warning, không reject)
MIN_ASSESSMENTS_COUNT = 3     # CRITICAL: EXACTLY 3 assessments per lesson (not >=3)
MAX_ASSESSMENTS_COUNT = 3     # CRITICAL: EXACTLY 3 assessments per lesson (not <=3)
MIN_ROADMAP_ITEMS = 2         # Minimum roadmap items
MAX_ROADMAP_ITEMS = 10        # Maximum roadmap items (prevent too many lessons)

# Recommendation System - OpenSearch indices
COURSE_VECTOR_INDEX = "pathlight-course-vectors"  # Store course embeddings (title + description)
QUIZ_VECTOR_INDEX = "pathlight-quiz-vectors"      # Store quiz embeddings (title + overview)
RECOMMENDATION_TOP_K = 10                         # Default top-k for recommendations