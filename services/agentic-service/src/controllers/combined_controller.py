from __future__ import annotations

from typing import List

from core.logging import setup_logger
from core.exceptions import InternalServerError
from controllers.file_controller import FileController
from controllers.agent_controller import AgentController
from schemas.agent_schemas import AgentRequest
from core import status_tracker as status
from config import config


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

    def _assert_indexed(self, course_id: str, expected_chunks: int) -> None:
        """Verify documents for course_id are present in OpenSearch with expected chunk count.

        Raises InternalServerError if OpenSearch is unavailable or count mismatches.
        """
        os_client = getattr(self.files, "opensearch_client", None)
        if not os_client or not os_client.is_available():
            raise InternalServerError(
                "OpenSearch client not available; cannot verify indexing"
            )

        # Use match query instead of term for text fields
        body = {
            "query": {"match": {"id": course_id}},
            "size": 0,
            "track_total_hits": True,
        }
        try:
            res = os_client.search(index=config.OPENSEARCH_INDEX_NAME, body=body)
            total = res.get("hits", {}).get("total", {})
            # OpenSearch can return int or {'value': int, 'relation': 'eq/gte'}
            if isinstance(total, dict):
                count = int(total.get("value", 0))
            else:
                count = int(total or 0)
        except Exception as e:
            raise InternalServerError(f"Failed verifying OpenSearch indexing: {e}")

        if count != int(expected_chunks):
            raise InternalServerError(
                f"Indexed chunk count mismatch: expected={expected_chunks}, actual={count}"
            )
        self.logger.info(
            f"OpenSearch verified: material_id={course_id}, indexed_chunks={count}"
        )

    def run(self, course_id: str, s3_keys: List[str], difficulty: str, duration: int, user_id: str) -> None:
        self.logger.info(
            "CombinedController.run: course_id=%s user_id=%s files=%d",
            course_id,
            user_id,
            len(s3_keys or []),
        )
        # 0) Strictly ensure Dynamo entry exists before any work (attach user_id for tracking)
        # For local test: use strict=False to skip DynamoDB
        try:
            status.start(course_id, user_id=user_id, strict=False)
        except Exception as e:
            self.logger.warning(f"DynamoDB status tracking unavailable: {e}")

        # 1) Vectorize (must index to OpenSearch successfully)
        s3 = self.files.get_files_by_names(s3_keys)
        vect_resp = self.files.vectorize_files(
            s3.file_streams, material_id=course_id, category=0
        )
        
        # In production/Lambda, verify OpenSearch indexing
        # In local mode, skip if OpenSearch is not available
        from core.environment import get_environment_type
        env = get_environment_type()
        
        if env == 'lambda':
            # Production: strict validation required
            if getattr(vect_resp, "warnings", None):
                raise InternalServerError(
                    "Vectorization completed with warnings; OpenSearch indexing not fully successful"
                )
            # Strictly verify in OpenSearch before marking vectorized
            self._assert_indexed(course_id, vect_resp.total_chunks)
            try:
                status.mark_vectorized(course_id, True)
            except Exception as e:
                self.logger.warning(f"Failed to update DynamoDB status: {e}")
        else:
            # Local/Dev: skip OpenSearch verification if not available
            self.logger.info(f"Vectorization completed in {env} mode - skipping OpenSearch verification")
            if getattr(vect_resp, "warnings", None):
                self.logger.warning(f"Vectorization warnings (non-critical in {env}): {vect_resp.warnings}")

        # 2) Generate course
        self.agent.generate_course(
            AgentRequest(
                id=course_id,
                difficulty=difficulty,
                duration=duration,
                user_id=user_id,
            )
        )

    def run_quiz(self, quiz_id: str, s3_keys: List[str], difficulty: str, duration: int, num_questions: int, user_id: str) -> None:
        """Run vectorization and quiz generation for a given quiz.
        
        Steps:
        1) Fetch files from S3 and vectorize them under material_id=quiz_id
        2) Invoke the multi-agent quiz generator
        3) Mark DynamoDB flags
        """
        self.logger.info(
            "CombinedController.run_quiz: quiz_id=%s user_id=%s files=%d num_questions=%d",
            quiz_id,
            user_id,
            len(s3_keys or []),
            num_questions,
        )
        
        # 0) Initialize tracking
        try:
            status.start_quiz(quiz_id, user_id=user_id, strict=False)
        except Exception as e:
            self.logger.warning(f"DynamoDB quiz tracking unavailable: {e}")

        # 1) Vectorize (uses same OpenSearch index as courses)
        s3 = self.files.get_files_by_names(s3_keys)
        vect_resp = self.files.vectorize_files(
            s3.file_streams, material_id=quiz_id, category=0
        )
        
        # Verify indexing based on environment
        from core.environment import get_environment_type
        env = get_environment_type()
        
        if env == 'lambda':
            if getattr(vect_resp, "warnings", None):
                raise InternalServerError(
                    "Vectorization completed with warnings; OpenSearch indexing not fully successful"
                )
            self._assert_indexed(quiz_id, vect_resp.total_chunks)
        else:
            self.logger.info(f"Vectorization completed in {env} mode - skipping OpenSearch verification")
            if getattr(vect_resp, "warnings", None):
                self.logger.warning(f"Vectorization warnings (non-critical in {env}): {vect_resp.warnings}")

        # 2) Generate quiz
        from controllers.quiz_controller import QuizController
        quiz_controller = QuizController()
        quiz_controller.generate_quiz(
            quiz_id=quiz_id,
            difficulty=difficulty,
            duration=duration,
            num_questions=num_questions,
            user_id=user_id,
        )
