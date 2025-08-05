"""
🧠 Embedding Service

Intelligent embedding creation with parallel processing and error handling.
Transforms text into meaningful vector representations.
"""

import asyncio
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from core.logging import setup_logger, log_exception
from core.exceptions import EmbeddingCreationError
from infrastructure.openai.client import OpenAIClient
from services.text_service import split_into_chunks
from schemas.vectorize_schemas import ChunkData, DocumentData


logger = setup_logger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding creation operation."""
    chunk_data: ChunkData
    success: bool
    error: Optional[str] = None


class EmbeddingService:
    """Professional embedding service with parallel processing."""
    
    def __init__(self, openai_client: OpenAIClient, max_tokens_per_chunk: int = 512):
        """
        Initialize embedding service.
        
        Args:
            openai_client: OpenAI client instance
            max_tokens_per_chunk: Maximum tokens per chunk
        """
        self.openai_client = openai_client
        self.max_tokens_per_chunk = max_tokens_per_chunk

    async def create_single_embedding(self, filename: str, chunk_idx: int, chunk: Dict) -> EmbeddingResult:
        """
        Create embedding for a single chunk.
        
        Args:
            filename: Source filename
            chunk_idx: Chunk index
            chunk: Chunk data
            
        Returns:
            EmbeddingResult
        """
        try:
            logger.info(f"Creating embedding for chunk {chunk_idx} of {filename}")
            
            embedding_data = await self.openai_client.create_embedding(chunk["chunk_text"])
            
            chunk_data = ChunkData(
                chunk_id=chunk["chunk_id"],
                embedding=embedding_data,
                chunk_text=chunk["chunk_text"]
            )
            
            return EmbeddingResult(
                chunk_data=chunk_data,
                success=True
            )
            
        except Exception as e:
            error_msg = f"Failed to create embedding for chunk {chunk_idx} in {filename}: {str(e)}"
            log_exception(logger, error_msg, e)
            return EmbeddingResult(
                chunk_data=None,
                success=False,
                error=error_msg
            )

    async def process_chunks_for_embeddings(self, filename: str, file_chunks: List[Dict]) -> Tuple[List[ChunkData], List[Dict]]:
        """
        Process chunks and create embeddings with parallel processing.
        
        Args:
            filename: Source filename
            file_chunks: List of text chunks
            
        Returns:
            Tuple of (chunk_data_list, embedding_errors)
        """
        chunks = []
        embedding_errors = []
        
        # Filter out empty chunks
        valid_chunks = []
        for chunk_idx, chunk in enumerate(file_chunks):
            if not chunk.get("chunk_text") or not chunk["chunk_text"].strip():
                logger.warning(f"Empty chunk {chunk_idx} in {filename}, skipping")
                continue
            valid_chunks.append((chunk_idx, chunk))
        
        if not valid_chunks:
            logger.warning(f"No valid chunks found in {filename}")
            return [], [{"filename": filename, "error": "No valid chunks found"}]
        
        # Create tasks for parallel embedding creation
        tasks = []
        for chunk_idx, chunk in valid_chunks:
            task = asyncio.create_task(self.create_single_embedding(filename, chunk_idx, chunk))
            tasks.append(task)
        
        # Process results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            chunk_idx, _ = valid_chunks[i]
            
            if isinstance(result, Exception):
                error_msg = f"Failed to create embedding for chunk {chunk_idx} in {filename}"
                log_exception(logger, error_msg, result)
                embedding_errors.append({
                    "filename": filename, 
                    "chunk_id": chunk_idx, 
                    "error": f"{error_msg}: {str(result)}"
                })
            elif isinstance(result, EmbeddingResult):
                if result.success:
                    chunks.append(result.chunk_data)
                else:
                    embedding_errors.append({
                        "filename": filename,
                        "chunk_id": chunk_idx,
                        "error": result.error
                    })
        
        return chunks, embedding_errors

    async def create_document_embeddings(self, file_contents: Dict[str, str]) -> Tuple[List[DocumentData], List[Dict]]:
        """
        Create embeddings for all documents.
        
        Args:
            file_contents: Dictionary of filename -> content
            
        Returns:
            Tuple of (documents, embedding_errors)
            
        Raises:
            EmbeddingCreationError: If no documents could be processed
        """
        documents = []
        embedding_errors = []
        count = 0
        
        for filename, content in file_contents.items():
            try:
                logger.info(f"Creating chunks for {filename}")
                file_chunks = split_into_chunks(
                    content, 
                    source_info=filename, 
                    max_tokens=self.max_tokens_per_chunk
                )
                
                if not file_chunks:
                    error_msg = f"No chunks generated for file: {filename}"
                    logger.warning(error_msg)
                    embedding_errors.append({"filename": filename, "error": error_msg})
                    continue
                
                chunks, chunk_errors = await self.process_chunks_for_embeddings(filename, file_chunks)
                
                # Extend embedding errors with chunk errors
                embedding_errors.extend(chunk_errors)
                
                if chunks:
                    documents.append(DocumentData(
                        document_id=count + 1,
                        document_source=filename,
                        chunks=chunks
                    ))
                    count += 1
                    logger.info(f"Successfully created {len(chunks)} embeddings for {filename}")
                else:
                    error_msg = f"No valid chunks with embeddings created for {filename}"
                    logger.warning(error_msg)
                    embedding_errors.append({"filename": filename, "error": error_msg})
                    
            except Exception as e:
                error_msg = f"Failed to process chunks for {filename}"
                log_exception(logger, error_msg, e)
                embedding_errors.append({"filename": filename, "error": f"{error_msg}: {str(e)}"})
                continue

        if not documents:
            raise EmbeddingCreationError(
                f"Failed to create embeddings for any documents. Errors: {embedding_errors}"
            )
        
        return documents, embedding_errors
