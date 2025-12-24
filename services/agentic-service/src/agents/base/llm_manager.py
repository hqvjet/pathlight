from schemas.context import State
from langchain_openai import ChatOpenAI
from langchain_core.prompts import FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import config

class LLMManager:
    """
    Manager for handling LLM instances with token optimization.
    """

    def __init__(self):
        self.api_key = config.OPENAI_API_KEY

    def get_llm(self, model_name: str, tools: list, enable_json_mode: bool = True) -> ChatOpenAI:
        """
        Get a ChatOpenAI instance with the specified model name and tools.
        
        Args:
            model_name: Model to use (e.g., "gpt-5-nano")
            tools: List of tools to bind
            enable_json_mode: Force JSON output to reduce tokens
        """
        llm_kwargs = {}
        
        # Token optimization: Enable JSON mode to force structured output
        if enable_json_mode:
            llm_kwargs["model_kwargs"] = {
                "response_format": {"type": "json_object"}
            }
        
        llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=self.api_key,
            temperature=0.3,  # Lower temperature for more consistent output
            **llm_kwargs
        )

        # Enable strict mode for tool schemas (required by OpenAI)
        llm = llm.bind_tools(tools, strict=True)
        return llm
