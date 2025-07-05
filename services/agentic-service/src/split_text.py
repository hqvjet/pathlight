def split_into_chunks(text, source_info, max_tokens=500):
    chunks = []
    current_chunk = ""
    current_token_count = 0
    chunk_id = 1

    for line in text.splitlines():
        estimated_tokens = len(line) // 4
        if current_token_count + estimated_tokens > max_tokens:
            chunks.append({
                "chunk_id": chunk_id,
                "chunk_text": current_chunk,
                "approx_token_count": current_token_count,
                "source_info": source_info
            })
            chunk_id += 1
            current_chunk = ""
            current_token_count = 0

        current_chunk += line + "\n"
        current_token_count += estimated_tokens

    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "chunk_text": current_chunk,
            "approx_token_count": current_token_count,
            "source_info": source_info
        })

    return chunks