"""
Chatbot Controller

Handles chatbot Q&A workflow: create record -> retrieve context -> generate answer -> update record.
"""

from __future__ import annotations

from typing import Dict, Any
from decimal import Decimal

from core.logging import setup_logger, log_exception
from core.exceptions import InternalServerError
from services.agentic.chatbot_service import ChatbotService
from infrastructure.aws.chatbot_dynamo_client import (
    create_chat_record,
    update_chat_status,
    ChatStatus,
)


logger = setup_logger(__name__)


class ChatbotController:
    """Controller for chatbot Q&A operations."""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.service = ChatbotService()
    
    def answer_question(
        self,
        chat_id: str,
        message: str,
        lesson_id: str,
        course_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Process chatbot question with full workflow:
        1. Create DynamoDB record with 'processing' status
        2. Retrieve context and generate answer
        3. Update record with 'done' or 'error' status
        
        Args:
            chat_id: Unique chat identifier
            message: User's question
            lesson_id: Lesson identifier
            course_id: Course identifier
            user_id: User identifier
            
        Returns:
            Dict with answer and metadata
        """
        self.logger.info(
            f"ChatbotController: chat_id={chat_id}, lesson={lesson_id}, course={course_id}, user={user_id}"
        )
        
        # Step 1: Create initial record with processing status
        success = create_chat_record(
            chat_id=chat_id,
            message=message,
            lesson_id=lesson_id,
            course_id=course_id,
            user_id=user_id,
        )
        
        if not success:
            self.logger.warning(f"Failed to create chat record for chat_id={chat_id}")
        
        try:
            # Step 2: Process question with RAG
            response = self.service.answer_question(
                chat_id=chat_id,
                message=message,
                lesson_id=lesson_id,
                course_id=course_id,
                user_id=user_id,
            )
            
            # Step 3: Update record with success status
            # Convert float to Decimal for DynamoDB
            context_chunks_data = [
                {
                    "chunk_text": chunk.chunk_text,
                    "document_source": chunk.document_source,
                    "score": Decimal(str(chunk.score)),
                }
                for chunk in response.context_chunks
            ]
            
            update_chat_status(
                chat_id=chat_id,
                status=ChatStatus.DONE,
                response=response.answer,
                context_chunks=context_chunks_data,
            )
            
            self.logger.info(
                f"Successfully answered question: chat_id={chat_id}, chunks={len(response.context_chunks)}"
            )
            
            return {
                "chat_id": chat_id,
                "answer": response.answer,
                "status": "done",
                "context_chunks": len(response.context_chunks),
            }
            
        except Exception as e:
            # Step 3 (error path): Update record with error status
            error_msg = str(e)
            log_exception(self.logger, f"Failed to answer question for chat_id={chat_id}", e)
            
            update_chat_status(
                chat_id=chat_id,
                status=ChatStatus.ERROR,
                error_message=error_msg,
            )
            
            # Re-raise to let SQS handler know about the failure
            raise InternalServerError(f"Chatbot processing failed: {error_msg}")
