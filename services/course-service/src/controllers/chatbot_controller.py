"""
Chatbot Controller for course-service.

Handles chatbot question submission and answer retrieval.
Questions are sent to SQS for async processing by agentic-service.
"""

import os
import uuid
from typing import Optional
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from schemas.course_schemas import (
    ChatbotQuestionRequest,
    ChatbotQuestionResponse,
    ChatbotAnswerResponse,
    ChatbotAnswerDetail,
    ChatContextChunk,
)
from services.sqs_publisher import send_chatbot_question


def _get_dynamodb_client():
    """Get DynamoDB client."""
    region = os.getenv("REGION", "ap-northeast-1")
    return boto3.client("dynamodb", region_name=region)


def _get_chat_table_name() -> str:
    """Get chat DynamoDB table name from environment."""
    return os.getenv("CHAT_TABLE_NAME", "pathlight-chat-dev")


class ChatbotController:
    """Controller for chatbot operations."""
    
    sqs_queue_url: str
    
    def __init__(self):
        queue_url = os.getenv("SQS_QUEUE_URL")
        if not queue_url:
            raise ValueError("SQS_QUEUE_URL environment variable not set")
        self.sqs_queue_url = queue_url
    
    def submit_question(
        self,
        request: ChatbotQuestionRequest,
        user_id: str,
    ) -> ChatbotQuestionResponse:
        """
        Submit a chatbot question for async processing.
        
        Creates a chat_id if not provided and sends message to SQS.
        
        Args:
            request: ChatbotQuestionRequest with question details
            user_id: User ID from authentication
            
        Returns:
            ChatbotQuestionResponse with chat_id and status
        """
        # Generate chat_id if not provided
        chat_id = request.chat_id or str(uuid.uuid4())
        
        try:
            # Send to SQS for async processing
            send_chatbot_question(
                queue_url=self.sqs_queue_url,
                chat_id=chat_id,
                message=request.message,
                lesson_id=request.lesson_id,
                course_id=request.course_id,
                user_id=user_id,
                chat_history=request.chat_history,
            )
            
            return ChatbotQuestionResponse(
                status=202,
                chat_id=chat_id,
                message="Question submitted for processing",
            )
        except Exception as e:
            raise RuntimeError(f"Failed to submit chatbot question: {str(e)}")
    
    def get_answer(
        self,
        chat_id: str,
        user_id: str,
    ) -> ChatbotAnswerResponse:
        """
        Get chatbot answer from DynamoDB.
        
        Args:
            chat_id: Chat session ID
            user_id: User ID for authorization
            
        Returns:
            ChatbotAnswerResponse with answer details or status
        """
        dynamodb = _get_dynamodb_client()
        table_name = _get_chat_table_name()
        
        try:
            response = dynamodb.get_item(
                TableName=table_name,
                Key={"chat_id": {"S": chat_id}}
            )
            
            if "Item" not in response:
                return ChatbotAnswerResponse(
                    status=404,
                    chat=None,
                    message="Chat not found"
                )
            
            item = response["Item"]
            
            # Check user authorization
            if item.get("user_id", {}).get("S") != user_id:
                return ChatbotAnswerResponse(
                    status=403,
                    chat=None,
                    message="Unauthorized"
                )
            
            status = item.get("status", {}).get("S", "processing")
            
            # If still processing, return processing status
            if status == "processing":
                return ChatbotAnswerResponse(
                    status=202,
                    chat=None,
                    message="Answer is being generated"
                )
            
            # If error, return error status
            if status == "error":
                return ChatbotAnswerResponse(
                    status=500,
                    chat=None,
                    message="Error generating answer"
                )
            
            # Parse context chunks if available
            context_chunks = []
            if "context_chunks" in item and "L" in item["context_chunks"]:
                for chunk_item in item["context_chunks"]["L"]:
                    if "M" in chunk_item:
                        chunk_map = chunk_item["M"]
                        context_chunks.append(
                            ChatContextChunk(
                                chunk_text=chunk_map.get("chunk_text", {}).get("S", ""),
                                document_source=chunk_map.get("document_source", {}).get("S", ""),
                                score=float(chunk_map.get("score", {}).get("N", "0")),
                            )
                        )
            
            # Build response with full details
            chat_detail = ChatbotAnswerDetail(
                chat_id=chat_id,
                message=item.get("message", {}).get("S", ""),
                answer=item.get("response", {}).get("S", ""),
                lesson_id=item.get("lesson_id", {}).get("S", ""),
                course_id=item.get("course_id", {}).get("S", ""),
                user_id=item.get("user_id", {}).get("S", ""),
                status=status,
                context_chunks=context_chunks,
                created_at=item.get("created_at", {}).get("S", ""),
                updated_at=item.get("updated_at", {}).get("S", ""),
            )
            
            return ChatbotAnswerResponse(
                status=200,
                chat=chat_detail,
                message="Answer retrieved successfully"
            )
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            raise RuntimeError(f"DynamoDB error ({error_code}): {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to get chatbot answer: {str(e)}")
