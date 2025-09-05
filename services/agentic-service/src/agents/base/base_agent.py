from core.logging import setup_logger
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from agents.base.prompt_manager import PromptManager


logger = setup_logger(__name__)

class BaseAgent:
    """
    Base class for all agents.
    This class should be inherited by all agent classes.
    It provides a common interface and basic functionality.
    """

    def __init__(self, name: str, foundation_model: str, prompt_manager: PromptManager):
        self.name = name
        self.foundation_model = foundation_model
        self.prompt_manager = prompt_manager

    def build_chain(self, llm: ChatOpenAI):
        # LangChain LLM for structured output
        prompt = self.prompt_manager.get_prompt(self.name)

        return prompt | llm

    def run(self, retrieved_data: list):
        """
        Run the agent with the given retrieved data.
        """
        self.log("info", f"[{self.name}] | RUN: {retrieved_data}")
        # Implement the agent's logic here

        self.log("info", f"Agent run completed.")
