import re
from typing import Set, Tuple, Optional
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


def normalize_query(query: str) -> str:
    """Normalize query for comparison by removing extra spaces and lowercasing."""
    if not query:
        return ""
    # Lowercase, remove extra whitespace, sort keywords for comparison
    words = sorted(set(query.lower().split()))
    return " ".join(words)


def extract_keywords(query: str) -> Set[str]:
    """Extract significant keywords from query for similarity detection."""
    if not query:
        return set()
    # Remove common filler words, keep meaningful keywords
    stopwords = {'the', 'a', 'an', 'is', 'are', 'of', 'to', 'for', 'and', 'or', 'in', 'on', 'at'}
    words = set(query.lower().split())
    return words - stopwords


def queries_are_similar(query1: str, query2: str, threshold: float = 0.7) -> bool:
    """Check if two queries are semantically similar based on keyword overlap."""
    kw1 = extract_keywords(query1)
    kw2 = extract_keywords(query2)
    if not kw1 or not kw2:
        return normalize_query(query1) == normalize_query(query2)
    # Jaccard similarity
    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)
    similarity = intersection / union if union > 0 else 0
    return similarity >= threshold


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
        # Key: (id, normalized_query) -> result
        self.retrieval_cache = {}
        # Track all queries per course_id for similarity check
        self.query_history: dict[str, list[str]] = {}  # {course_id: [query1, query2, ...]}
        
    def get_tools(self, agent_name: str) -> list:
        if agent_name not in self.tool_map:
            raise ValueError(f"No tools found for agent: {agent_name}")

        return self.tool_map[agent_name]
    
    def _find_similar_cached_query(self, course_id: str, query: str) -> Optional[str]:
        """Find if a similar query was already executed for this course."""
        if course_id not in self.query_history:
            return None
        for prev_query in self.query_history[course_id]:
            if queries_are_similar(query, prev_query):
                return prev_query
        return None

    def execute_tool_sync(self, tool_name: str, args: dict) -> str:
        """Execute tool synchronously with smart caching and duplicate detection."""
        # Token optimization: Check cache for retrieval_tool
        if tool_name == "retrieval_tool":
            course_id = args.get("id", "")
            query = args.get("query", "")
            normalized = normalize_query(query)
            cache_key = (course_id, normalized)
            
            # Check exact cache hit
            if cache_key in self.retrieval_cache:
                logger.info(f"Cache HIT for query: {query[:50]}...")
                # Return with explicit message to STOP calling same query
                cached_result = self.retrieval_cache[cache_key]
                return f"[ĐÃ TRUY VẤN TRƯỚC ĐÓ - KHÔNG GỌI LẠI] Kết quả được cache:\n\n{cached_result}\n\n[HÀNH ĐỘNG BẮT BUỘC: Sử dụng thông tin trên để tạo output JSON ngay. KHÔNG gọi retrieval_tool với query tương tự nữa.]"
            
            # Check similarity with previous queries
            similar_query = self._find_similar_cached_query(course_id, query)
            if similar_query:
                similar_key = (course_id, normalize_query(similar_query))
                if similar_key in self.retrieval_cache:
                    logger.warning(f"Similar query detected! Original: '{similar_query[:50]}...' New: '{query[:50]}...'")
                    cached_result = self.retrieval_cache[similar_key]
                    return f"[QUERY TƯƠNG TỰ ĐÃ ĐƯỢC GỌI - DỪNG LẠI] Query '{query[:30]}...' rất giống với query trước đó.\n\nKết quả từ query tương tự:\n{cached_result}\n\n[HÀNH ĐỘNG BẮT BUỘC: Bạn đã có đủ thông tin. TẠO OUTPUT JSON NGAY BÂY GIỜ. KHÔNG gọi thêm retrieval_tool.]"
            
            # Cache miss - execute and cache
            logger.info(f"Cache MISS for query: {query[:50]}...")
            
            # Track this query in history
            if course_id not in self.query_history:
                self.query_history[course_id] = []
            self.query_history[course_id].append(query)
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in tools.")

        tool = self.tools[tool_name]
        result = tool._run(**args)
        
        # Cache retrieval results
        if tool_name == "retrieval_tool":
            course_id = args.get("id", "")
            query = args.get("query", "")
            normalized = normalize_query(query)
            cache_key = (course_id, normalized)
            self.retrieval_cache[cache_key] = result
        
        return result
    
    def clear_cache_for_course(self, course_id: str):
        """Clear cache for a specific course (useful for retries)."""
        keys_to_remove = [k for k in self.retrieval_cache if k[0] == course_id]
        for k in keys_to_remove:
            del self.retrieval_cache[k]
        if course_id in self.query_history:
            del self.query_history[course_id]