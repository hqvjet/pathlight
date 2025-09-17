import re
from agents.base.public_tools import RetrievalTool
from constant import (
    FINAL_TEST_CREATOR_AGENT_NAME,
    LESSON_CREATOR_AGENT_NAME,
    ORCHESTRATOR_AGENT_NAME,
    PLANNER_AGENT_NAME,
    TEST_CREATOR_AGENT_NAME
)


class ToolManager:
    def __init__(self):
        self.tools = {
            "retrieval_tool": RetrievalTool(),
        }
        self.tool_map = {
            PLANNER_AGENT_NAME: [self.tools["retrieval_tool"]],
            ORCHESTRATOR_AGENT_NAME: [self.tools["retrieval_tool"]],
            FINAL_TEST_CREATOR_AGENT_NAME: [self.tools["retrieval_tool"]],
            LESSON_CREATOR_AGENT_NAME: [self.tools["retrieval_tool"]],
            TEST_CREATOR_AGENT_NAME: [self.tools["retrieval_tool"]],
        }
        
    def get_tools(self, agent_name: str) -> list:
        if agent_name not in self.tool_map:
            raise ValueError(f"No tools found for agent: {agent_name}")

        return self.tool_map[agent_name]

    async def execute_tool(self, tool_name: str, args: dict) -> str:
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in tools.")

        tool = self.tools[tool_name]
        return await tool._arun(**args)