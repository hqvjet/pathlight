from schemas.context import State
from langchain_openai import ChatOpenAI
from langchain_core.prompts import FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import config

class LLMManager:
    """
    Manager for handling LLM instances.
    """

    def __init__(self):
        self.api_key = config.OPENAI_API_KEY

    def get_llm(self, model_name: str, tools: list) -> ChatOpenAI:
        """
        Get a ChatOpenAI instance with the specified model name and tools.
        """
        llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=self.api_key
        )

        llm = llm.bind_tools(tools)
        return llm
