# from dotenv import load_dotenv
# load_dotenv(override=True)  # Override existing .env variables
from typing import Type
from pydantic import BaseModel
from langchain_core.tools import BaseTool
import json

from infrastructure.clients import clients as shared_clients
from config import config
from schemas.agent_schemas import RetrievalArgs, S3UploadArgs

class RetrievalTool(BaseTool):
    """
    A tool for retrieving information from a knowledge base.
    """

    name: str = "retrieval_tool"
    description: str = "A tool to retrieve information from a knowledge base."
    args_schema: Type[BaseModel] = RetrievalArgs

    # def __init__(self):
    #     pass
    
    def _run(self, *args, **kwargs) -> str:
        raise RuntimeError(
            "retrieval_tool chỉ hỗ trợ async. Hãy chạy graph bằng .ainvoke(...) "
            "để ToolNode gọi _arun."
        )

    async def _arun(self, id: str, query: str, k: int ) -> str:
        """
        Run the retrieval tool with the given query.
        """
        print(f"[Retrieval Tool] - Invoked with id: {id}, query: {query}, k: {k}")
        if not id or not query or not k:
            raise ValueError("id, query, and k must be provided.")

        embedding = await shared_clients.openai.create_embedding(text=query)
        if not isinstance(embedding, list):
            embedding = list(embedding)

        # Preferred: legacy-compatible KNN with post_filter by id (id is keyword per mapping)
        body_legacy = {
            "size": 5,
            "query": {
                "knn": {
                    "documents.chunks.embedding": {
                        "vector": embedding,
                        "k": 5
                    }
                }
            },
            "post_filter": {"term": {"id": id}},
            "_source": [
                "id", "category",
                "documents.document_id", "documents.document_source",
                "documents.chunks.chunk_id", "documents.chunks.chunk_text"
            ],
        }

        result = json.dumps(await shared_clients.opensearch.search(
            index=config.OPENSEARCH_INDEX_NAME,
            body=body_legacy,
        ))
        return result

class S3Uploader(BaseTool):
    """
    A tool for uploading files to S3.
    """

    name: str = "s3_uploader"
    description: str = "A tool to upload files to S3."
    args_schema: Type[BaseModel] = S3UploadArgs

    def _run(self, *args, **kwargs) -> str:
        raise RuntimeError(
            "s3_uploader chỉ hỗ trợ async. Hãy chạy graph bằng .ainvoke(...) "
            "để ToolNode gọi _arun."
        )

    async def _arun(self, key: str, json_content: str) -> str:
        """
        Run the S3 uploader tool with the given parameters.
        """
        print(f"[S3 Uploader] - Invoked with key: {key}")
        if not key or not json_content:
            raise ValueError("key and json_content must be provided.")

        shared_clients.s3.upload_file(bucket_name=config.S3_BUCKET_NAME, filename=key, content=json_content)
        return "Upload successful"

# Quick manual test (optional). Run this module directly to test.
# if __name__ == "__main__":
#     import asyncio
#     async def _test():
#         tool = RetrievalTool()
#         print(await tool.arun("485935534", "Nêu rõ cuộc thi hackathon vpbank 2025"))
#     asyncio.run(_test())