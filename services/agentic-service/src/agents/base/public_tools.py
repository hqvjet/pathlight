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
        
        # Preferred: legacy-compatible KNN with post_filter by id (id is keyword per mapping)
        body_legacy = {
            "size": k,
            "query": {
                "knn": {
                    "documents.chunks.embedding": {
                        "vector": embedding,
                        "k": k
                    }
                }
            },
            "post_filter": {"term": {"id": id}},
            "_source": [
                "documents.chunks.chunk_text"
            ],
        }

        result = shared_clients.opensearch.search(
            index=config.OPENSEARCH_INDEX_NAME,
            body=body_legacy,
        )
        
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