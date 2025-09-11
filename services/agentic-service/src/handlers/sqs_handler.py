"""
SQS event handler for agentic-service.

Parses AWS SQS batch events and dispatches to appropriate workflows.
Returns Lambda batch failure response format.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from core.logging import setup_logger, log_exception
from core.exceptions import AgenticServiceError, create_error_response
from contracts.sqs_contracts import (
    MessageType,
    VectorizeMessage,
    GenerateCourseMessage,
    SQSBatchResponse,
    SQSEvent,
)
from schemas.vectorize_schemas import VectorizeRequest
from schemas.agent_schemas import AgentRequest


logger = setup_logger(__name__)


def _handle_vectorize(msg: VectorizeMessage) -> None:
    # Lazy import to avoid initializing AWS clients at module import time
    from controllers.file_controller import FileController
    controller = FileController()
    s3 = controller.get_files_by_names(msg.payload.s3_keys)
    # Reuse existing service to vectorize
    import asyncio

    async def _run():
        await controller.vectorize_files(
            s3.file_streams,
            msg.payload.material_id,
            msg.payload.category,
        )

    asyncio.run(_run())


def _handle_generate_course(msg: GenerateCourseMessage) -> None:
    from controllers.agent_controller import AgentController
    controller = AgentController()
    import asyncio

    async def _run():
        await controller.generate_course(
            AgentRequest(
                id=msg.payload.id,
                difficulty=msg.payload.difficulty,
                duration=msg.payload.duration,
            )
        )

    asyncio.run(_run())


def process_sqs_event(event: SQSEvent) -> SQSBatchResponse:
    """Process AWS SQS batch event and return batchItemFailures on error per record."""
    failures: List[dict] = []

    for record in event.Records:
        message_id = record.messageId
        body = record.body
        try:
            data = json.loads(body) if isinstance(body, str) else body
            msg_type = MessageType(data.get("type"))
            if msg_type == MessageType.VECTORIZE_MATERIAL:
                msg = VectorizeMessage(**data)
                _handle_vectorize(msg)
            elif msg_type == MessageType.GENERATE_COURSE:
                msg = GenerateCourseMessage(**data)
                _handle_generate_course(msg)
            else:
                raise ValueError(f"Unsupported message type: {data.get('type')}")
        except Exception as e:
            log_exception(logger, f"Failed processing record {message_id}", e)
            # Add to batchItemFailures to let SQS retry (or DLQ)
            failures.append({"itemIdentifier": message_id})

    return SQSBatchResponse(batchItemFailures=failures)
