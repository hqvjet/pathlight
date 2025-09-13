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
        # Start status row early
        try:
            status.start(course_id)
        except Exception:
            pass

        # 1) Vectorize
        try:
            s3 = self.files.get_files_by_names(s3_keys)
            await self.files.vectorize_files(s3.file_streams, material_id=course_id, category=0)
            try:
                status.mark_vectorized(course_id, True)
            except Exception:
                pass
        except Exception as e:
            self.logger.exception("Vectorization step failed: %s", e)
            # Do not abort the whole combined flow; continue to generation

        # 2) Generate course
        await self.agent.generate_course(
            AgentRequest(id=course_id, difficulty=difficulty, duration=duration, user_id=user_id)
        )
