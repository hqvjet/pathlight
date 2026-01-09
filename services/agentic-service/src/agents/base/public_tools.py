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
        
        FIXED: Proper vector similarity search with material_id filter.
        Uses 2-step approach: 
        1. Fetch all chunks for material_id with embeddings
        2. Compute cosine similarity in Python and rank
        """

        if not id or not query or not k:
            raise ValueError("id, query, and k must be provided.")

        # Create embedding for the query - now sync function (no await)
        query_embedding = shared_clients.openai.create_embedding(text=query)
        if not isinstance(query_embedding, list):
            query_embedding = list(query_embedding)

        # Limit k to max 8 to prevent token explosion
        k = min(k, 8)
        
        # Step 1: Fetch ALL chunks for this material_id with embeddings
        # We need embeddings to compute similarity, so fetch more than k
        fetch_size = min(k * 20, 200)  # Fetch 20x more to rank, max 200
        
        body = {
            "size": fetch_size,
            "query": {
                "term": {"id": id}
            },
            "_source": [
                "documents.chunks.chunk_text",
                "documents.chunks.embedding"
            ],
        }
        
        # Execute search - filter only, no KNN yet
        result = shared_clients.opensearch.search(
            index=config.OPENSEARCH_INDEX_NAME,
            body=body,
        )
        
        total_hits = result.get("hits", {}).get("total", {}).get("value", 0)
        
        if total_hits == 0:
            logger.warning(f"No chunks found for material_id={id}")
            return "No relevant information found for this material."

        # Step 2: Extract chunks with embeddings and compute similarity
        import numpy as np
        
        chunk_data = []
        for hit in result.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            for doc in source.get("documents", []):
                for chunk in doc.get("chunks", []):
                    text = chunk.get("chunk_text", "").strip()
                    embedding = chunk.get("embedding", [])
                    
                    if text and embedding and len(embedding) == len(query_embedding):
                        # Compute cosine similarity
                        query_vec = np.array(query_embedding)
                        chunk_vec = np.array(embedding)
                        
                        # Cosine similarity = dot product / (norm1 * norm2)
                        similarity = np.dot(query_vec, chunk_vec) / (
                            np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
                        )
                        
                        chunk_data.append({
                            'text': text,
                            'similarity': float(similarity)
                        })
        
        if not chunk_data:
            logger.warning(f"No valid chunks with embeddings for material_id={id}")
            return "No relevant information found for this query."
        
        # Step 3: Sort by similarity (highest first) and take top k
        chunk_data.sort(key=lambda x: x['similarity'], reverse=True)
        top_chunks = chunk_data[:k]
        
        # Extract just the text
        chunks = [item['text'] for item in top_chunks]
        
        # Limit total characters to prevent token overflow
        MAX_CHARS = 6000  # ~1500 tokens
        combined = "\n\n---\n\n".join(chunks)
        
        logger.info(
            f"Retrieved {len(chunks)} chunks for query: {query[:60]}... "
            f"(avg similarity: {np.mean([x['similarity'] for x in top_chunks]):.3f})"
        )
        
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