# from dotenv import load_dotenv
# load_dotenv(override=True)  # Override existing .env variables
from typing import Type
from pydantic import BaseModel
from langchain_core.tools import BaseTool
import json

from infrastructure.clients import clients as shared_clients
from config import config
from schemas.agent_schemas import RetrievalArgs, S3UploadArgs, S3ReadArgs

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
        # print(f"[Retrieval Tool] - Invoked with id: {id}, query: {query}, k: {k}")
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
        # print(f"[S3 Uploader] - Invoked with key: {key}")
        if not key or not json_content:
            raise ValueError("key and json_content must be provided.")

        # Lightweight quality gate for lesson files to avoid uploading thin content
        try:
            parsed = json.loads(json_content)
        except Exception:
            parsed = None

        if isinstance(parsed, dict) and isinstance(parsed.get("lessons"), list):
            violations = []
            required_sections = ["Mục tiêu", "Khái niệm", "Ví dụ", "Thực hành", "Lỗi thường gặp", "Tham khảo"]
            for idx, lesson in enumerate(parsed["lessons"], start=1):
                name = lesson.get("lesson_name") or f"Lesson-{idx}"
                content = lesson.get("lesson_content") or ""
                lines = content.splitlines()
                if len(lines) < 50:
                    violations.append({
                        "lesson": name,
                        "issue": f"lesson_content quá ngắn: {len(lines)} dòng (< 50)"
                    })
                missing = [sec for sec in required_sections if sec not in content]
                if missing:
                    violations.append({
                        "lesson": name,
                        "issue": f"thiếu mục: {', '.join(missing)}"
                    })
            if violations:
                return json.dumps({
                    "status": "VALIDATION_FAILED",
                    "message": "Nội dung bài học chưa đạt tiêu chí độ dài/cấu trúc. Hãy mở rộng và thử upload lại.",
                    "violations": violations,
                    "expected": {
                        "min_lines": 50,
                        "required_sections": required_sections
                    }
                }, ensure_ascii=False)

        shared_clients.s3.upload_file(bucket_name=config.S3_BUCKET_NAME, filename=key, content=json_content)
        return "# **Upload the content to s3 successful**"

class S3Reader(BaseTool):
    """
    A tool for reading JSON files from S3.
    """

    name: str = "s3_reader"
    description: str = "A tool to read JSON files from S3 by key."
    args_schema: Type[BaseModel] = S3ReadArgs

    def _run(self, *args, **kwargs) -> str:
        raise RuntimeError(
            "s3_reader chỉ hỗ trợ async. Hãy chạy graph bằng .ainvoke(...) "
            "để ToolNode gọi _arun."
        )

    async def _arun(self, key: str) -> str:
        if not key:
            raise ValueError("key must be provided.")

        stream, meta, err = shared_clients.s3.get_file_safely(
            bucket_name=config.S3_BUCKET_NAME,
            filename=key,
            max_size_bytes=2 * 1024 * 1024  # 2MB
        )
        if err:
            raise RuntimeError(f"Failed to read S3 object {key}: {err}")

        content = stream.getvalue().decode('utf-8') if stream else ""
        # Return raw content string; let the agent parse JSON as needed
        return content

# Quick manual test (optional). Run this module directly to test.
# if __name__ == "__main__":
#     import asyncio
#     async def _test():
#         tool = RetrievalTool()
#         print(await tool.arun("485935534", "Nêu rõ cuộc thi hackathon vpbank 2025"))
#     asyncio.run(_test())