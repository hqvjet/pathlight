from math import e
from langchain_core.prompts import PromptTemplate

from utils import read_yaml_file
from constant import (
    FINAL_TEST_CREATOR_AGENT_NAME, 
    ORCHESTRATOR_AGENT_NAME, 
    LESSON_CREATOR_AGENT_NAME, 
    PLANNER_AGENT_NAME, 
    TEST_CREATOR_AGENT_NAME
)

class PromptManager:
    def __init__(self):
        self.catalog = read_yaml_file("agents/prompts/catalog.yaml")
        self.ai_prompts = {
            PLANNER_AGENT_NAME: self.catalog['planner']['prompt_path'],
            FINAL_TEST_CREATOR_AGENT_NAME: self.catalog['final_test_creator']['prompt_path'],
            # ORCHESTRATOR_AGENT_NAME: self.catalog['orchestrator']['prompt_path'],
            LESSON_CREATOR_AGENT_NAME: self.catalog['lesson_creator']['prompt_path'],
            TEST_CREATOR_AGENT_NAME: self.catalog['test_creator']['prompt_path'],
        }

    def get_prompt(self, agent_name: str) -> PromptTemplate:
        """Get the prompt template for a specific agent.

        Args:
            agent_name (str): The name of the agent.

        Raises:
            ValueError: If no prompt is found for the agent.

        Returns:
            PromptTemplate: The prompt template for the agent.
        """
        if agent_name not in self.ai_prompts:
            raise ValueError(f"No prompt found for agent: {agent_name}")

        prompt = read_yaml_file(f"agents/prompts/{self.ai_prompts[agent_name]}")

        example_prompt = PromptTemplate(
            input_variables=prompt['variables'],
            template=prompt['prompt']
        )

        return example_prompt