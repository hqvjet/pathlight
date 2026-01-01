from schemas.context import State
from langchain_openai import ChatOpenAI
from langchain_core.prompts import FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import config
from constant import LLM_REQUEST_TIMEOUT, LLM_TEMPERATURE

class LLMManager:
    """
    Manager for handling LLM instances with token optimization.
    """

    def __init__(self):
        self.api_key = config.OPENAI_API_KEY

    def get_llm(self, model_name: str, tools: list, enable_json_mode: bool = True, max_tokens: int = None) -> ChatOpenAI:
        """
        Get a ChatOpenAI instance with the specified model name and tools.
        
        Args:
            model_name: Model to use (e.g., "gpt-5-nano")
            tools: List of tools to bind
            enable_json_mode: Force JSON output to reduce tokens
            max_tokens: Max completion tokens (None = no limit, use default per agent)
        """
        llm_kwargs = {}
        
        # CRITICAL: Enable JSON mode to force structured output
        if enable_json_mode:
            llm_kwargs["model_kwargs"] = {
                "response_format": {"type": "json_object"}
            }
        
        # CRITICAL FIX: max_tokens based on agent type
        # Planner needs more tokens for roadmap JSON
        # Lesson/Test creators need moderate tokens
        # Default: None (no limit) to prevent truncation
        llm_params = {
            "model_name": model_name,
            "openai_api_key": self.api_key,
            "temperature": LLM_TEMPERATURE,  # CRITICAL: 0 for deterministic output
            "request_timeout": LLM_REQUEST_TIMEOUT,  # CRITICAL: Timeout from constant.py
            "max_retries": 1,  # Reduce retries to fail fast
        }
        
        # Only set max_tokens if explicitly provided
        if max_tokens is not None:
            llm_params["max_tokens"] = max_tokens
        
        llm = ChatOpenAI(**llm_params, **llm_kwargs)

        # Enable strict mode for tool schemas (required by OpenAI)
        llm = llm.bind_tools(tools, strict=True)
        return llm
