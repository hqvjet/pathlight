import re
from agents.base.public_tools import RetrievalTool
from constant import (
    LESSON_CREATOR_AGENT_NAME,
    ORCHESTRATOR_AGENT_NAME,
    PLANNER_AGENT_NAME,
    TEST_CREATOR_AGENT_NAME,
    QUIZ_PLANNER_AGENT_NAME,
    QUESTIONER_AGENT_NAME
)
from core.logging import setup_logger

logger = setup_logger(__name__)


class ToolManager:
    def __init__(self):
        self.tools = {
            "retrieval_tool": RetrievalTool(),
        }
        self.tool_map = {
            PLANNER_AGENT_NAME: [self.tools["retrieval_tool"]],
            ORCHESTRATOR_AGENT_NAME: [self.tools["retrieval_tool"]],
            LESSON_CREATOR_AGENT_NAME: [self.tools["retrieval_tool"]],
            TEST_CREATOR_AGENT_NAME: [self.tools["retrieval_tool"]],
            QUIZ_PLANNER_AGENT_NAME: [self.tools["retrieval_tool"]],
            QUESTIONER_AGENT_NAME: [self.tools["retrieval_tool"]],
        }
        
        # Token optimization: Cache retrieval results
        self.retrieval_cache = {}  # {(id, query): result}
        
    def get_tools(self, agent_name: str) -> list:
        if agent_name not in self.tool_map:
            raise ValueError(f"No tools found for agent: {agent_name}")

        return self.tool_map[agent_name]

    def execute_tool_sync(self, tool_name: str, args: dict) -> str:
        """Execute tool synchronously with caching for retrieval."""
        # Token optimization: Check cache for retrieval_tool
        if tool_name == "retrieval_tool":
            cache_key = (args.get("id"), args.get("query"))
            if cache_key in self.retrieval_cache:
                logger.info(f"Cache HIT for query: {args.get('query', '')[:50]}...")
                return self.retrieval_cache[cache_key]
            
            # Cache miss - execute and cache
            logger.info(f"Cache MISS for query: {args.get('query', '')[:50]}...")
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in tools.")

        tool = self.tools[tool_name]
        result = tool._run(**args)
        
        # Cache retrieval results
        if tool_name == "retrieval_tool":
            cache_key = (args.get("id"), args.get("query"))
            self.retrieval_cache[cache_key] = result
        
        return result