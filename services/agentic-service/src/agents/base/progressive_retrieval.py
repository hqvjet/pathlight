"""
Progressive Retrieval Module - Hardcoded 3-Layer Strategy

This module forces deterministic 3-layer retrieval without relying on LLM reasoning.
Layer 1: Scout with universal keywords
Layer 2: Dig into main topic extracted from Layer 1
Layer 3: Dig into secondary topic or examples
"""

from typing import List, Dict, Tuple
import re
from collections import Counter


def extract_top_keywords(text: str, top_n: int = 3) -> List[str]:
    """
    Extract top N keywords/phrases from retrieval text.
    Uses simple frequency analysis + noun phrase extraction.
    
    Args:
        text: Retrieved text content
        top_n: Number of top keywords to extract
        
    Returns:
        List of top keywords/phrases
    """
    # Remove special chars, normalize
    text = text.lower()
    text = re.sub(r'[<>=/\[\]{}()]', ' ', text)
    
    # Extract potential keywords (2-4 word phrases or single meaningful words)
    # Focus on capitalized words (likely important terms)
    words = text.split()
    
    # Filter out common stop words
    stop_words = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
        'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'of', 'to', 'in', 'for',
        'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then',
        'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'and', 'but', 'or',
        'page', 'number', 'chapter', 'section', 'figure', 'table', 'book', 'author',
        'also', 'however', 'therefore', 'thus', 'này', 'là', 'của', 'và', 'có',
        'được', 'trong', 'với', 'theo', 'để', 'cho', 'từ', 'trên', 'về', 'các'
    }
    
    # Extract meaningful words (3+ chars, not stop words)
    meaningful_words = [
        w for w in words 
        if len(w) >= 3 and w not in stop_words and not w.isdigit()
    ]
    
    # Count frequency
    word_freq = Counter(meaningful_words)
    
    # Get top N most common
    top_keywords = [word for word, count in word_freq.most_common(top_n * 2)]
    
    # Try to extract multi-word phrases (bigrams that appear together)
    bigrams = []
    for i in range(len(meaningful_words) - 1):
        bigram = f"{meaningful_words[i]} {meaningful_words[i+1]}"
        if len(bigram) > 8:  # Filter out too short bigrams
            bigrams.append(bigram)
    
    bigram_freq = Counter(bigrams)
    top_bigrams = [phrase for phrase, count in bigram_freq.most_common(top_n) if count > 1]
    
    # Combine: prefer bigrams, then single words
    result = []
    result.extend(top_bigrams[:top_n])
    
    # Add single words to fill up to top_n
    for word in top_keywords:
        if len(result) >= top_n:
            break
        if word not in ' '.join(result):  # Don't add if already in bigram
            result.append(word)
    
    return result[:top_n]


def build_layer1_query() -> str:
    """
    Build Layer 1 scout query with universal structure keywords.
    This query targets document structure and overview.
    """
    return (
        '"Table of Contents" "Mục lục" "Abstract" "Overview" '
        '"Introduction" "Summary" "Tóm tắt" "Giới thiệu" '
        '"Agenda" "Main topics" "Conclusion"'
    )


def build_layer2_query(layer1_text: str, context_title: str = "") -> str:
    """
    Build Layer 2 query to dig into specific topic.
    Use context_title (lesson description from planner) as primary seed.
    
    Args:
        layer1_text: Text retrieved from Layer 1
        context_title: Lesson description/title from planner (SEED for each lesson)
        
    Returns:
        Query string for Layer 2
    """
    # PRIORITY 1: If context_title exists, extract keywords from it
    if context_title and len(context_title.strip()) > 5:
        context_topics = extract_top_keywords(context_title, top_n=2)
        if context_topics:
            main_topic = context_topics[0]
            # Also extract from Layer 1 for enrichment
            layer1_topics = extract_top_keywords(layer1_text, top_n=1)
            secondary_topic = layer1_topics[0] if layer1_topics else main_topic
            
            # Build query combining lesson-specific topic + Layer 1 context
            return (
                f'"{main_topic}" "{secondary_topic}" "definition" "explanation" "details" '
                f'"architecture" "structure" "how it works" "components"'
            )
    
    # PRIORITY 2: Fallback to Layer 1 extraction if no meaningful context_title
    topics = extract_top_keywords(layer1_text, top_n=2)
    
    if not topics:
        # Last resort: generic query
        return '"concepts" "definitions" "main points" "details" "explanation"'
    
    main_topic = topics[0]
    
    # Build query focusing on main topic details
    return (
        f'"{main_topic}" "definition" "explanation" "details" '
        f'"architecture" "structure" "how it works" "components"'
    )


def build_layer3_query(layer1_text: str, layer2_query: str, context_title: str = "") -> str:
    """
    Build Layer 3 query for secondary topic or examples.
    
    Args:
        layer1_text: Text from Layer 1
        layer2_query: Query used in Layer 2 (to avoid overlap)
        context_title: Optional context
        
    Returns:
        Query string for Layer 3
    """
    # Extract topics from Layer 1
    topics = extract_top_keywords(layer1_text, top_n=3)
    
    # Find topic NOT used in Layer 2
    main_topic = topics[0] if topics else context_title
    secondary_topic = None
    
    for topic in topics[1:]:
        if topic not in layer2_query:
            secondary_topic = topic
            break
    
    if secondary_topic:
        # Strategy A: Dig into secondary topic
        return (
            f'"{secondary_topic}" "explanation" "details" '
            f'"use cases" "implementation" "examples"'
        )
    else:
        # Strategy B: Get examples/applications of main topic
        return (
            f'"{main_topic}" "examples" "applications" '
            f'"case study" "practical" "real world" "ví dụ" "ứng dụng"'
        )


def execute_progressive_retrieval(
    retrieval_tool_func,
    material_id: str,
    context_title: str = "",
    k: int = 5
) -> Dict[str, str]:
    """
    Execute full 3-layer progressive retrieval with hardcoded strategy.
    
    Args:
        retrieval_tool_func: Function to call for retrieval (should accept query, material_id, k)
        material_id: Material ID to retrieve from
        context_title: Optional title for context (lesson title, course title)
        k: Number of chunks to retrieve per layer
        
    Returns:
        Dict with keys: layer1_text, layer2_text, layer3_text, all_text
    """
    results = {}
    
    # Layer 1: Scout
    layer1_query = build_layer1_query()
    layer1_result = retrieval_tool_func(query=layer1_query, material_id=material_id, k=k)
    results['layer1_text'] = layer1_result
    results['layer1_query'] = layer1_query
    
    # Layer 2: Dig main topic
    layer2_query = build_layer2_query(layer1_result, context_title)
    layer2_result = retrieval_tool_func(query=layer2_query, material_id=material_id, k=k)
    results['layer2_text'] = layer2_result
    results['layer2_query'] = layer2_query
    
    # Layer 3: Dig secondary or examples
    layer3_query = build_layer3_query(layer1_result, layer2_query, context_title)
    layer3_result = retrieval_tool_func(query=layer3_query, material_id=material_id, k=k)
    results['layer3_text'] = layer3_result
    results['layer3_query'] = layer3_query
    
    # Combine all text
    results['all_text'] = f"""
=== LAYER 1 RETRIEVAL (Structure Scout) ===
Query: {layer1_query}

{layer1_result}

=== LAYER 2 RETRIEVAL (Main Topic Deep Dive) ===
Query: {layer2_query}

{layer2_result}

=== LAYER 3 RETRIEVAL (Secondary Topic / Examples) ===
Query: {layer3_query}

{layer3_result}
"""
    
    return results
