"""
SQS event handler for agentic-service.

Parses AWS SQS batch events and dispatches to appropriate workflows.
Returns Lambda batch failure response format.
"""

from __future__ import annotations

import json
from math import log
from typing import List

from core.logging import setup_logger, log_exception
from core.exceptions import AgenticServiceError
from contracts.sqs_contracts import (
    MessageType,
    GenerateCourseWithVectorizeMessage,
    ChatbotQuestionMessage,
    SQSBatchResponse,
    SQSEvent,
)


logger = setup_logger(__name__)


def _handle_generate_course_with_vectorize(msg: GenerateCourseWithVectorizeMessage) -> None:
    # Validate required fields
    if not msg.payload.user_id:
        raise ValueError(f"user_id is required for course {msg.payload.id}")
    
    from controllers.combined_controller import CombinedController
    controller = CombinedController()
    controller.run(
        course_id=msg.payload.id,
        s3_keys=msg.payload.s3_keys,
        difficulty=msg.payload.difficulty,
        duration=msg.payload.duration,
        user_id=msg.payload.user_id,
    )


def _handle_chatbot_question(msg: ChatbotQuestionMessage) -> None:
    """Handle chatbot Q&A message."""
    # Validate required fields
    if not msg.payload.chat_id:
        raise ValueError("chat_id is required")
    if not msg.payload.message:
        raise ValueError("message is required")
    if not msg.payload.lesson_id:
        raise ValueError("lesson_id is required")
    if not msg.payload.course_id:
        raise ValueError("course_id is required")
    if not msg.payload.user_id:
        raise ValueError("user_id is required")
    
    from controllers.chatbot_controller import ChatbotController
    controller = ChatbotController()
    controller.answer_question(
        chat_id=msg.payload.chat_id,
        message=msg.payload.message,
        lesson_id=msg.payload.lesson_id,
        course_id=msg.payload.course_id,
        user_id=msg.payload.user_id,
    )


def process_sqs_event(event: SQSEvent) -> SQSBatchResponse:
    """Process AWS SQS batch event and return batchItemFailures on error per record."""
    failures: List[dict] = []

    for record in event.Records:
        message_id = record.messageId
        body = record.body
        try:
            data = json.loads(body) if isinstance(body, str) else body
            msg_type = MessageType(data.get("type"))
            if msg_type == MessageType.GENERATE_COURSE_WITH_VECTORIZE:
                msg = GenerateCourseWithVectorizeMessage(**data)
                logger.info(
                    f"Processing GENERATE_COURSE_WITH_VECTORIZE: id={msg.payload.id}, files={len(msg.payload.s3_keys)}, duration={msg.payload.duration}, difficulty={msg.payload.difficulty}"
                )
                _handle_generate_course_with_vectorize(msg)
            elif msg_type == MessageType.CHATBOT_QUESTION:
                msg = ChatbotQuestionMessage(**data)
                logger.info(
                    f"Processing CHATBOT_QUESTION: chat_id={msg.payload.chat_id}, lesson_id={msg.payload.lesson_id}, course_id={msg.payload.course_id}"
                )
                _handle_chatbot_question(msg)
            else:
                raise ValueError(f"Unsupported message type: {data.get('type')}")
        except Exception as e:
            log_exception(logger, f"Failed processing record {message_id}", e)
            # Add to batchItemFailures to let SQS retry (or DLQ)
            failures.append({"itemIdentifier": message_id})

    return SQSBatchResponse(batchItemFailures=failures)
