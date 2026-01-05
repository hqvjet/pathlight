"""
Chatbot RAG Service for Lesson Q&A

Retrieves relevant context from lesson knowledge base and generates answers.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from core.logging import setup_logger, log_exception
from core.exceptions import InternalServerError
from config import config
from infrastructure.clients import clients
from persistence.course_persistence import get_lesson_content


logger = setup_logger(__name__)


class ContextChunk(BaseModel):
    """Retrieved context chunk from knowledge base."""
    chunk_text: str
    document_source: str
    score: float


class ChatbotResponse(BaseModel):
    """Response from chatbot service."""
    answer: str
    context_chunks: List[ContextChunk]
    model: str = "gpt-4o-mini"


class ChatbotService:
    """Service for answering questions using RAG from lesson knowledge base."""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.opensearch_client = clients.opensearch
        self.openai_client = clients.openai
        self.index_name = config.OPENSEARCH_INDEX_NAME
        
    def retrieve_context(
        self, 
        lesson_id: str, 
        course_id: str, 
        query: str, 
        top_k: int = 5
    ) -> List[ContextChunk]:
        """
        Retrieve relevant context from lesson knowledge base using vector search.
        
        Args:
            lesson_id: Lesson identifier
            course_id: Course identifier (used as material_id in OpenSearch)
            query: User's question
            top_k: Number of top results to retrieve
            
        Returns:
            List of context chunks with relevance scores
        """
        if not self.opensearch_client or not self.opensearch_client.is_available():
            self.logger.warning("OpenSearch client not available for RAG")
            return []
        
        try:
            # Create embedding for the query
            query_embedding = self.openai_client.create_embedding(query)
            
            # Build KNN search query for the specific course (material_id)
            # Using script_score query to combine KNN search with filtering by course_id
            search_body = {
                "size": top_k,
                "query": {
                    "script_score": {
                        "query": {
                            "term": {
                                "id": course_id  # Filter by course_id (material_id)
                            }
                        },
                        "script": {
                            "source": "knn_score",
                            "lang": "knn",
                            "params": {
                                "field": "documents.chunks.embedding",
                                "query_value": query_embedding,
                                "space_type": "cosinesimil"
                            }
                        }
                    }
                },
                "_source": ["documents.chunks.chunk_text", "documents.document_source", "id"]
            }
            
            self.logger.info(
                f"Searching OpenSearch for lesson_id={lesson_id}, course_id={course_id}, top_k={top_k}"
            )
            
            response = self.opensearch_client.search(
                index=self.index_name,
                body=search_body
            )
            
            # Extract chunks from response
            chunks = []
            hits = response.get("hits", {}).get("hits", [])
            
            for hit in hits:
                score = hit.get("_score", 0.0)
                source = hit.get("_source", {})
                documents = source.get("documents", [])
                
                # Extract all chunks from documents
                for doc in documents:
                    doc_source = doc.get("document_source", "Unknown")
                    for chunk in doc.get("chunks", []):
                        chunk_text = chunk.get("chunk_text", "")
                        if chunk_text:
                            chunks.append(
                                ContextChunk(
                                    chunk_text=chunk_text,
                                    document_source=doc_source,
                                    score=score
                                )
                            )
            
            self.logger.info(f"Retrieved {len(chunks)} context chunks for query")
            return chunks[:top_k]  # Limit to top_k
            
        except Exception as e:
            log_exception(self.logger, "Failed to retrieve context from OpenSearch", e)
            return []
    
    def generate_answer(
        self,
        query: str,
        lesson_content: dict,
        context_chunks: List[ContextChunk],
        lesson_id: str,
    ) -> str:
        """
        Generate answer using lesson content and retrieved context from RAG.
        
        Args:
            query: User's question
            lesson_content: Lesson data from database (main source)
            context_chunks: Retrieved context chunks from RAG (supplementary)
            lesson_id: Lesson identifier for context
            
        Returns:
            Generated answer
        """
        # Primary source: Lesson content from database
        if not lesson_content:
            if not context_chunks:
                return (
                    "I don't have access to this lesson's content. "
                    "Please ensure the lesson exists and try again."
                )
            # Fallback to RAG only if no lesson content
            return self._generate_from_rag_only(query, context_chunks, lesson_id)
        
        # Build main content from lesson
        lesson_text = f"""
Lesson: {lesson_content.get('title', 'Untitled')}

Overview:
{lesson_content.get('overview', 'No overview available')}

Content:
{lesson_content.get('content', 'No content available')}
"""
        
        # Build supplementary context from RAG (if available)
        rag_context = ""
        if context_chunks:
            rag_parts = []
            for i, chunk in enumerate(context_chunks[:3], 1):  # Limit to top 3
                rag_parts.append(
                    f"[Additional Context {i} from {chunk.document_source}]:\n{chunk.chunk_text}\n"
                )
            rag_context = "\n".join(rag_parts)
        
        # Build prompt for GPT
        system_prompt = (
            "You are a helpful teaching assistant for an online course. "
            "Answer the student's question based on the lesson content provided. "
            "Use the additional context from course materials if relevant. "
            "Be clear, concise, and educational. If the content doesn't contain "
            "enough information to answer the question, say so politely and suggest "
            "what topics are covered in the lesson."
        )
        
        user_prompt = f"""Based on the following lesson content, please answer the student's question.

LESSON CONTENT:
{lesson_text}
"""
        
        if rag_context:
            user_prompt += f"""
ADDITIONAL CONTEXT FROM COURSE MATERIALS:
{rag_context}
"""
        
        user_prompt += f"""
Student's question: {query}

Please provide a helpful and accurate answer based on the lesson content above."""
        
        try:
            # Use OpenAI chat completion
            response = self.openai_client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            
            answer = response.choices[0].message.content.strip()
            self.logger.info(f"Generated answer for lesson_id={lesson_id}")
            return answer
            
        except Exception as e:
            log_exception(self.logger, "Failed to generate answer with GPT", e)
            raise InternalServerError(f"Failed to generate answer: {str(e)}")
    
    def _generate_from_rag_only(
        self,
        query: str,
        context_chunks: List[ContextChunk],
        lesson_id: str,
    ) -> str:
        """Fallback: Generate answer using only RAG context (when lesson content unavailable)."""
        if not context_chunks:
            return (
                "I don't have enough information to answer this question. "
                "Please try rephrasing your question or ask about content covered in the lesson."
            )
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            context_parts.append(
                f"[Context {i} from {chunk.document_source}]:\n{chunk.chunk_text}\n"
            )
        context_text = "\n".join(context_parts)
        
        # Build prompt for GPT
        system_prompt = (
            "You are a helpful teaching assistant for an online course. "
            "Answer the student's question based on the provided lesson context. "
            "Be clear, concise, and educational. If the context doesn't contain "
            "enough information to answer the question, say so politely."
        )
        
        user_prompt = f"""Based on the following lesson context, please answer the student's question.

Context from lesson materials:
{context_text}

Student's question: {query}

Please provide a helpful and accurate answer based on the context above."""
        
        try:
            # Use OpenAI chat completion
            response = self.openai_client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            
            answer = response.choices[0].message.content.strip()
            self.logger.info(f"Generated answer for lesson_id={lesson_id}")
            return answer
            
        except Exception as e:
            log_exception(self.logger, "Failed to generate answer with GPT", e)
            raise InternalServerError(f"Failed to generate answer: {str(e)}")
    
    def answer_question(
        self,
        chat_id: str,
        message: str,
        lesson_id: str,
        course_id: str,
        user_id: str,
    ) -> ChatbotResponse:
        """
        Answer user's question using RAG from lesson knowledge base.
        
        Args:
            chat_id: Chat identifier
            message: User's question
            lesson_id: Lesson identifier
            course_id: Course identifier
            user_id: User identifier
            
        Returns:
            ChatbotResponse with answer and context chunks
        """
        self.logger.info(
            f"Processing chatbot question: chat_id={chat_id}, lesson_id={lesson_id}, course_id={course_id}"
        )
        
        # Step 1: Get lesson content from database (primary source)
        lesson_content = get_lesson_content(lesson_id)
        
        # Step 2: Retrieve additional context from RAG (supplementary)
        context_chunks = self.retrieve_context(
            lesson_id=lesson_id,
            course_id=course_id,
            query=message,
            top_k=5
        )
        
        # Step 3: Generate answer using lesson content + RAG context
        answer = self.generate_answer(
            query=message,
            lesson_content=lesson_content,
            context_chunks=context_chunks,
            lesson_id=lesson_id
        )
        
        return ChatbotResponse(
            answer=answer,
            context_chunks=context_chunks,
            model="gpt-4o-mini"
        )
