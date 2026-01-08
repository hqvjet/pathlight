"""OpenSearch index mappings for recommendation system.

Defines mappings for:
- pathlight-course-vectors: Course embeddings for recommendations
- pathlight-quiz-vectors: Quiz embeddings for recommendations
"""

# Course vector index mapping
COURSE_VECTOR_MAPPING = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100
        }
    },
    "mappings": {
        "properties": {
            "course_id": {"type": "keyword"},
            "title": {"type": "text"},
            "description": {"type": "text"},
            "vector": {
                "type": "knn_vector",
                "dimension": 1536,  # text-embedding-3-small dimension
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib",
                    "parameters": {
                        "ef_construction": 128,
                        "m": 24
                    }
                }
            },
            "user_id": {"type": "keyword"},
            "publish": {"type": "boolean"},
            "level": {"type": "keyword"},
            "duration": {"type": "integer"}
        }
    }
}

# Quiz vector index mapping
QUIZ_VECTOR_MAPPING = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100
        }
    },
    "mappings": {
        "properties": {
            "quiz_id": {"type": "keyword"},
            "title": {"type": "text"},
            "overview": {"type": "text"},
            "vector": {
                "type": "knn_vector",
                "dimension": 1536,  # text-embedding-3-small dimension
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib",
                    "parameters": {
                        "ef_construction": 128,
                        "m": 24
                    }
                }
            },
            "user_id": {"type": "keyword"},
            "publish": {"type": "boolean"},
            "level": {"type": "keyword"},
            "duration": {"type": "integer"},
            "num_questions": {"type": "integer"}
        }
    }
}
