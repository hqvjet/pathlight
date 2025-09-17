from __future__ import annotations

import asyncio
from typing import List

from core.logging import setup_logger
from core.exceptions import InternalServerError
from controllers.file_controller import FileController
from controllers.agent_controller import AgentController
from schemas.agent_schemas import AgentRequest
from core import status_tracker as status


class CombinedController:
    """Run vectorization and course generation in one call for a given course.

    Steps:
    1) Fetch files from S3 and vectorize them under material_id=course_id.
    2) Invoke the multi-agent course generator.
    3) Mark DynamoDB flags (vectorized true, plus the normal agent flags).
    """

    def __init__(self) -> None:
        self.logger = setup_logger(__name__)
        self.files = FileController()
        self.agent = AgentController()

    async def run(self, course_id: str, s3_keys: List[str], difficulty: str, duration: int, user_id: str) -> None:
        # 0) Strictly ensure Dynamo entry exists before any work
        status.start(course_id, strict=True)

        # 1) Vectorize (must index to OpenSearch successfully)
        s3 = self.files.get_files_by_names(s3_keys)
        vect_resp = await self.files.vectorize_files(s3.file_streams, material_id=course_id, category=0)
        # Consider any warnings as failures for the requirement "only mark vectorize=true when docs pushed to OpenSearch"
        if getattr(vect_resp, "warnings", None):
            raise InternalServerError("Vectorization completed with warnings; OpenSearch indexing not fully successful")
        status.mark_vectorized(course_id, True)

        # 2) Generate course
        await self.agent.generate_course(
            AgentRequest(id=course_id, difficulty=difficulty, duration=duration, user_id=user_id)
        )
