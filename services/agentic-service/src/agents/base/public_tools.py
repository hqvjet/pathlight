# from dotenv import load_dotenv
# load_dotenv(override=True)  # Override existing .env variables
from typing import Type
from pydantic import BaseModel
from langchain_core.tools import BaseTool
import json
import asyncio

from infrastructure.clients import clients as shared_clients
from config import config
from schemas.agent_schemas import RetrievalArgs
from core.logging import setup_logger

logger = setup_logger(__name__)

class RetrievalTool(BaseTool):
    """
    A tool for retrieving information from a knowledge base.
    """

    name: str = "retrieval_tool"
    description: str = "A tool to retrieve information from a knowledge base."
    args_schema: Type[BaseModel] = RetrievalArgs

    def _run(self, id: str, query: str, k: int) -> str:
        """
        Synchronous wrapper for async retrieval.
        Runs the async _arun method in a new event loop.
        """
        # Create new event loop for sync execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._arun(id, query, k))
        finally:
            loop.close()

    async def _arun(self, id: str, query: str, k: int ) -> str:
        """
        Run the retrieval tool with the given query.
        Returns ONLY extracted text chunks, not full JSON (token optimization).
        """

        if not id or not query or not k:
            raise ValueError("id, query, and k must be provided.")

        # Create embedding - now sync function (no await)
        embedding = shared_clients.openai.create_embedding(text=query)
        if not isinstance(embedding, list):
            embedding = list(embedding)

        # Limit k to max 8 to prevent token explosion
        k = min(k, 8)
        
        # FIX: Filter first, then KNN on filtered results
        body_legacy = {
            "size": k,
            "query": {
                "bool": {
                    "filter": {
                        "term": {
                            "id": id
                        }
                    },
                    "must": {
                        "knn": {
                            "documents.chunks.embedding": {
                                "vector": embedding,
                                "k": 10000  # High k to search all filtered docs
                            }
                        }
                    }
                }
            },
            "_source": [
                "documents.chunks.chunk_text"
            ],
        }
        
        # Execute search with filter
        result = shared_clients.opensearch.search(
            index=config.OPENSEARCH_INDEX_NAME,
            body=body_legacy,
        )
        
        total_hits = result.get("hits", {}).get("total", {}).get("value", 0)
        
        if total_hits == 0:
            logger.warning(f"No chunks found for material_id={id}")

        # Extract ONLY text chunks to reduce tokens (10k → 2k)
        chunks = []
        for hit in result.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            for doc in source.get("documents", []):
                for chunk in doc.get("chunks", []):
                    text = chunk.get("chunk_text", "").strip()
                    if text:
                        chunks.append(text)
        
        if not chunks:
            return "No relevant information found for this query."
        
        # Limit total characters to prevent token overflow
        MAX_CHARS = 6000  # ~1500 tokens
        combined = "\n\n---\n\n".join(chunks)
        
        logger.info(f"Retrieved {len(chunks)} chunks for query: {query[:60]}...")
        
        if len(combined) > MAX_CHARS:
            combined = combined[:MAX_CHARS] + "\n\n[... truncated for token optimization ...]"
        
        return combined

# Quick manual test (optional). Run this module directly to test.
# if __name__ == "__main__":
#     import asyncio
#     async def _test():
#         tool = RetrievalTool()
#         print(await tool.arun("485935534", "Nêu rõ cuộc thi hackathon vpbank 2025"))
#     asyncio.run(_test())