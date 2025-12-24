"""
Context Compressor - Compress retrieval results để giảm tokens

Sử dụng gpt-5-nano để compress context từ 2k tokens → 500 tokens
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from core.logging import setup_logger
from config import config

logger = setup_logger(__name__)

class ContextCompressor:
    """Compress retrieval results để giảm tokens while preserving key information."""
    
    def __init__(self, model_name: str = "gpt-5-nano"):
        """Initialize compressor với cheap model."""
        self.compressor = ChatOpenAI(
            model_name=model_name,
            openai_api_key=config.OPENAI_API_KEY,
            temperature=0,
            model_kwargs={"response_format": {"type": "text"}}
        )
        logger.info(f"ContextCompressor initialized with {model_name}")
    
    def compress(self, retrieved_text: str, query: str, max_tokens: int = 500) -> str:
        """
        Compress retrieved text xuống max_tokens.
        
        Args:
            retrieved_text: Raw text from retrieval tool
            query: Original query để focus compression
            max_tokens: Target token limit
            
        Returns:
            Compressed text with key information only
        """
        # Quick check: if already short, return as-is
        estimated_tokens = len(retrieved_text) // 4
        if estimated_tokens <= max_tokens:
            return retrieved_text
        
        logger.info(f"Compressing {estimated_tokens} tokens → {max_tokens} tokens for query: {query[:50]}...")
        
        prompt = f"""Trích xuất ONLY thông tin liên quan đến: "{query}"

Văn bản gốc:
{retrieved_text}

Yêu cầu:
- Chỉ giữ facts trả lời trực tiếp query
- Loại bỏ thông tin trùng lặp
- Dùng bullet points ngắn gọn
- Tối đa {max_tokens} tokens (~{max_tokens * 4} ký tự)
- Giữ nguyên ngôn ngữ gốc

Thông tin trích xuất:"""

        try:
            response = self.compressor.invoke([
                SystemMessage(content="Bạn là chuyên gia trích xuất thông tin chính xác và súc tích."),
                HumanMessage(content=prompt)
            ])
            
            compressed = response.content.strip()
            logger.info(f"Compression successful: {estimated_tokens} → {len(compressed) // 4} tokens")
            return compressed
            
        except Exception as e:
            logger.warning(f"Compression failed: {e}, returning original text truncated")
            # Fallback: truncate if compression fails
            max_chars = max_tokens * 4
            if len(retrieved_text) > max_chars:
                return retrieved_text[:max_chars] + "\n\n[... truncated ...]"
            return retrieved_text
    
    async def acompress(self, retrieved_text: str, query: str, max_tokens: int = 500) -> str:
        """Async version of compress."""
        # Quick check: if already short, return as-is
        estimated_tokens = len(retrieved_text) // 4
        if estimated_tokens <= max_tokens:
            return retrieved_text
        
        logger.info(f"Compressing {estimated_tokens} tokens → {max_tokens} tokens for query: {query[:50]}...")
        
        prompt = f"""Trích xuất ONLY thông tin liên quan đến: "{query}"

Văn bản gốc:
{retrieved_text}

Yêu cầu:
- Chỉ giữ facts trả lời trực tiếp query
- Loại bỏ thông tin trùng lặp
- Dùng bullet points ngắn gọn
- Tối đa {max_tokens} tokens (~{max_tokens * 4} ký tự)
- Giữ nguyên ngôn ngữ gốc

Thông tin trích xuất:"""

        try:
            response = await self.compressor.ainvoke([
                SystemMessage(content="Bạn là chuyên gia trích xuất thông tin chính xác và súc tích."),
                HumanMessage(content=prompt)
            ])
            
            compressed = response.content.strip()
            logger.info(f"Compression successful: {estimated_tokens} → {len(compressed) // 4} tokens")
            return compressed
            
        except Exception as e:
            logger.warning(f"Compression failed: {e}, returning original text truncated")
            # Fallback: truncate if compression fails
            max_chars = max_tokens * 4
            if len(retrieved_text) > max_chars:
                return retrieved_text[:max_chars] + "\n\n[... truncated ...]"
            return retrieved_text
