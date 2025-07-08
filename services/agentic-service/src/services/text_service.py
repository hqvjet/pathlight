from typing import List, Dict, Any


def split_into_chunks(text: str, source_info: str, max_tokens: int = 500) -> List[Dict[str, Any]]:
    """
    Split text into chunks with approximate token limits.
    
    Args:
        text: The text content to split
        source_info: Information about the source (filename, etc.)
        max_tokens: Maximum number of tokens per chunk
        
    Returns:
        List[Dict]: List of text chunks with metadata
    """
    chunks = []
    current_chunk = ""
    current_token_count = 0
    chunk_id = 1

    for line in text.splitlines():
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = len(line) // 4
        
        # If adding this line would exceed max tokens, save current chunk
        if current_token_count + estimated_tokens > max_tokens and current_chunk:
            chunks.append({
                "chunk_id": chunk_id,
                "chunk_text": current_chunk.strip(),
                "approx_token_count": current_token_count,
                "chunk_source": source_info
            })
            chunk_id += 1
            current_chunk = ""
            current_token_count = 0

        current_chunk += line + "\n"
        current_token_count += estimated_tokens

    # Add the last chunk if it has content
    if current_chunk.strip():
        chunks.append({
            "chunk_id": chunk_id,
            "chunk_text": current_chunk.strip(),
            "approx_token_count": current_token_count,
            "chunk_source": source_info
        })

    return chunks
