import re
from agents.base.public_tools import RetrievalTool, S3Uploader
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
            "s3_uploader": S3Uploader()
        }
        self.tool_map = {
            PLANNER_AGENT_NAME: [self.tools["retrieval_tool"], self.tools["s3_uploader"]],
            ORCHESTRATOR_AGENT_NAME: [self.tools["retrieval_tool"], self.tools["s3_uploader"]],
            FINAL_TEST_CREATOR_AGENT_NAME: [self.tools["retrieval_tool"], self.tools["s3_uploader"]],
            LESSON_CREATOR_AGENT_NAME: [self.tools["retrieval_tool"], self.tools["s3_uploader"]],
            TEST_CREATOR_AGENT_NAME: [self.tools["retrieval_tool"], self.tools["s3_uploader"]],
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