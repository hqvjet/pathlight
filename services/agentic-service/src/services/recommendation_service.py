"""Recommendation service for course/quiz suggestions based on user profile.

Architecture:
- User profile vector = average of all user's course/quiz vectors
- Course/Quiz vector = embedding(title + description/overview)
- Similarity search in OpenSearch to find top-k recommendations

OpenSearch Indices:
- pathlight-course-vectors: {course_id, title, description, vector, user_id, publish, level, duration}
- pathlight-quiz-vectors: {quiz_id, title, overview, vector, user_id, publish, level, duration, num_questions}
"""

from typing import List, Dict, Optional, Tuple
import numpy as np

from core.logging import setup_logger
from constant import COURSE_VECTOR_INDEX, QUIZ_VECTOR_INDEX, RECOMMENDATION_TOP_K

logger = setup_logger(__name__)


class RecommendationService:
    def __init__(self):
        self.os_client = None
        self.openai_client = None
        
    def _get_os_client(self):
        """Lazy load OpenSearch client."""
        if self.os_client is None:
            from infrastructure.clients import clients
            self.os_client = clients.opensearch
        return self.os_client
        
    def _get_openai_client(self):
        """Lazy load OpenAI client."""
        if self.openai_client is None:
            from infrastructure.clients import clients
            self.openai_client = clients.openai
        return self.openai_client
        
    def compute_text_embedding(self, text: str) -> List[float]:
        """Compute embedding for text using OpenAI API.
        
        Args:
            text: Text to embed (e.g., "title. description")
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            client = self._get_openai_client()
            return client.create_embedding(text)
        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")
            raise
            
    def index_course_vector(
        self,
        course_id: str,
        title: str,
        description: str,
        user_id: str,
        publish: bool,
        level: str,
        duration: int
    ) -> None:
        """Compute and index course vector to OpenSearch.
        
        Args:
            course_id: Unique course identifier
            title: Course title
            description: Course description/overview
            user_id: Owner user ID
            publish: Whether course is public
            level: Difficulty level
            duration: Duration in minutes
        """
        os_client = self._get_os_client()
        if not os_client or not os_client.is_available():
            logger.warning("OpenSearch not available - skipping course vector indexing")
            return
            
        try:
            # Compute embedding
            text = f"{title}. {description}"
            vector = self.compute_text_embedding(text)
            
            # Index document
            doc = {
                "course_id": course_id,
                "title": title,
                "description": description,
                "vector": vector,
                "user_id": user_id,
                "publish": publish,
                "level": level,
                "duration": duration,
            }
            
            os_client.index_document(
                index_name=COURSE_VECTOR_INDEX,
                document=doc,
                doc_id=course_id
            )
            logger.info(f"Indexed course vector: {course_id}")
            
        except Exception as e:
            logger.error(f"Failed to index course vector {course_id}: {e}")
            # Don't raise - indexing is best-effort
            
    def index_quiz_vector(
        self,
        quiz_id: str,
        title: str,
        overview: str,
        user_id: str,
        publish: bool,
        level: str,
        duration: int,
        num_questions: int
    ) -> None:
        """Compute and index quiz vector to OpenSearch.
        
        Args:
            quiz_id: Unique quiz identifier
            title: Quiz title
            overview: Quiz overview
            user_id: Owner user ID
            publish: Whether quiz is public
            level: Difficulty level
            duration: Duration in minutes
            num_questions: Number of questions
        """
        os_client = self._get_os_client()
        if not os_client or not os_client.is_available():
            logger.warning("OpenSearch not available - skipping quiz vector indexing")
            return
            
        try:
            # Compute embedding
            text = f"{title}. {overview}"
            vector = self.compute_text_embedding(text)
            
            # Index document
            doc = {
                "quiz_id": quiz_id,
                "title": title,
                "overview": overview,
                "vector": vector,
                "user_id": user_id,
                "publish": publish,
                "level": level,
                "duration": duration,
                "num_questions": num_questions,
            }
            
            os_client.index_document(
                index_name=QUIZ_VECTOR_INDEX,
                document=doc,
                doc_id=quiz_id
            )
            logger.info(f"Indexed quiz vector: {quiz_id}")
            
        except Exception as e:
            logger.error(f"Failed to index quiz vector {quiz_id}: {e}")
            
    def compute_user_profile_vector(self, user_id: str) -> Optional[List[float]]:
        """Compute user profile vector as average of all user's course/quiz vectors.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile vector (average of course/quiz vectors) or None if user has no content
        """
        os_client = self._get_os_client()
        if not os_client or not os_client.is_available():
            logger.error("OpenSearch not available")
            return None
            
        try:
            vectors = []
            
            # Get all courses by user
            course_query = {
                "query": {"term": {"user_id": user_id}},
                "size": 1000,
                "_source": ["vector"]
            }
            
            course_results = os_client.search(
                index=COURSE_VECTOR_INDEX,
                body=course_query
            )
            
            for hit in course_results.get("hits", {}).get("hits", []):
                vec = hit["_source"].get("vector")
                if vec:
                    vectors.append(vec)
                    
            # Get all quizzes by user
            quiz_query = {
                "query": {"term": {"user_id": user_id}},
                "size": 1000,
                "_source": ["vector"]
            }
            
            quiz_results = os_client.search(
                index=QUIZ_VECTOR_INDEX,
                body=quiz_query
            )
            
            for hit in quiz_results.get("hits", {}).get("hits", []):
                vec = hit["_source"].get("vector")
                if vec:
                    vectors.append(vec)
                    
            if not vectors:
                logger.warning(f"No vectors found for user {user_id}")
                return None
                
            # Compute average
            avg_vector = np.mean(vectors, axis=0).tolist()
            logger.info(f"Computed user profile vector from {len(vectors)} items")
            return avg_vector
            
        except Exception as e:
            logger.error(f"Failed to compute user profile vector: {e}")
            return None
            
    def recommend_courses(
        self,
        user_vector: List[float],
        top_k: int = RECOMMENDATION_TOP_K,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Recommend courses based on user profile vector.
        
        Args:
            user_vector: User profile vector
            top_k: Number of recommendations to return
            filters: Additional filters (e.g., {"level": "medium", "publish": True})
            
        Returns:
            List of recommended courses with metadata
        """
        os_client = self._get_os_client()
        if not os_client or not os_client.is_available():
            logger.error("OpenSearch not available")
            return []
            
        try:
            # Build query with k-NN similarity search
            query = {
                "size": top_k,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "knn": {
                                    "vector": {
                                        "vector": user_vector,
                                        "k": top_k
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            # Add filters if provided
            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    filter_clauses.append({"term": {key: value}})
                query["query"]["bool"]["filter"] = filter_clauses
                
            # Execute search
            results = os_client.search(
                index=COURSE_VECTOR_INDEX,
                body=query
            )
            
            # Format results
            recommendations = []
            for hit in results.get("hits", {}).get("hits", []):
                source = hit["_source"]
                recommendations.append({
                    "course_id": source.get("course_id"),
                    "title": source.get("title"),
                    "description": source.get("description"),
                    "level": source.get("level"),
                    "duration": source.get("duration"),
                    "score": hit.get("_score", 0.0)
                })
                
            logger.info(f"Found {len(recommendations)} course recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend courses: {e}")
            return []
            
    def recommend_quizzes(
        self,
        user_vector: List[float],
        top_k: int = RECOMMENDATION_TOP_K,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Recommend quizzes based on user profile vector.
        
        Args:
            user_vector: User profile vector
            top_k: Number of recommendations to return
            filters: Additional filters (e.g., {"level": "easy", "publish": True})
            
        Returns:
            List of recommended quizzes with metadata
        """
        os_client = self._get_os_client()
        if not os_client or not os_client.is_available():
            logger.error("OpenSearch not available")
            return []
            
        try:
            # Build query with k-NN similarity search
            query = {
                "size": top_k,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "knn": {
                                    "vector": {
                                        "vector": user_vector,
                                        "k": top_k
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            # Add filters if provided
            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    filter_clauses.append({"term": {key: value}})
                query["query"]["bool"]["filter"] = filter_clauses
                
            # Execute search
            results = os_client.search(
                index=QUIZ_VECTOR_INDEX,
                body=query
            )
            
            # Format results
            recommendations = []
            for hit in results.get("hits", {}).get("hits", []):
                source = hit["_source"]
                recommendations.append({
                    "quiz_id": source.get("quiz_id"),
                    "title": source.get("title"),
                    "overview": source.get("overview"),
                    "level": source.get("level"),
                    "duration": source.get("duration"),
                    "num_questions": source.get("num_questions"),
                    "score": hit.get("_score", 0.0)
                })
                
            logger.info(f"Found {len(recommendations)} quiz recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend quizzes: {e}")
            return []
    
    def recommend_courses_by_ids(
        self,
        user_vector: List[float],
        course_ids: List[str],
        top_k: int = RECOMMENDATION_TOP_K
    ) -> List[Tuple[str, float]]:
        """Recommend courses from a specific list of course IDs.
        
        This is used when course service provides a list of public course IDs
        to search within (e.g., only published courses).
        
        Args:
            user_vector: User profile vector
            course_ids: List of course IDs to search within
            top_k: Number of recommendations to return
            
        Returns:
            List of (course_id, sim_score) tuples, sorted by score descending
        """
        os_client = self._get_os_client()
        if not os_client or not os_client.is_available():
            logger.error("OpenSearch not available")
            return []
            
        try:
            # Build query with k-NN search + filter by course IDs
            query = {
                "size": top_k,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "knn": {
                                    "vector": {
                                        "vector": user_vector,
                                        "k": top_k * 2  # Fetch more for filtering
                                    }
                                }
                            }
                        ],
                        "filter": [
                            {
                                "terms": {
                                    "course_id": course_ids
                                }
                            }
                        ]
                    }
                },
                "_source": ["course_id"]  # Only need course_id
            }
            
            # Execute search
            results = os_client.search(
                index=COURSE_VECTOR_INDEX,
                body=query
            )
            
            # Format as [(course_id, score), ...] sorted by score descending
            recommendations = []
            for hit in results.get("hits", {}).get("hits", []):
                course_id = hit["_source"].get("course_id")
                score = hit.get("_score", 0.0)
                recommendations.append((course_id, score))
                
            # Sort by score descending and limit to top_k
            recommendations.sort(key=lambda x: x[1], reverse=True)
            recommendations = recommendations[:top_k]
            
            logger.info(f"Found {len(recommendations)} course recommendations from {len(course_ids)} candidates")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend courses by IDs: {e}")
            return []
    
    def recommend_quizzes_by_ids(
        self,
        user_vector: List[float],
        quiz_ids: List[str],
        top_k: int = RECOMMENDATION_TOP_K
    ) -> List[Tuple[str, float]]:
        """Recommend quizzes from a specific list of quiz IDs.
        
        This is used when quiz service provides a list of public quiz IDs
        to search within (e.g., only published quizzes).
        
        Args:
            user_vector: User profile vector
            quiz_ids: List of quiz IDs to search within
            top_k: Number of recommendations to return
            
        Returns:
            List of (quiz_id, sim_score) tuples, sorted by score descending
        """
        os_client = self._get_os_client()
        if not os_client or not os_client.is_available():
            logger.error("OpenSearch not available")
            return []
            
        try:
            # Build query with k-NN search + filter by quiz IDs
            query = {
                "size": top_k,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "knn": {
                                    "vector": {
                                        "vector": user_vector,
                                        "k": top_k * 2  # Fetch more for filtering
                                    }
                                }
                            }
                        ],
                        "filter": [
                            {
                                "terms": {
                                    "quiz_id": quiz_ids
                                }
                            }
                        ]
                    }
                },
                "_source": ["quiz_id"]  # Only need quiz_id
            }
            
            # Execute search
            results = os_client.search(
                index=QUIZ_VECTOR_INDEX,
                body=query
            )
            
            # Format as [(quiz_id, score), ...] sorted by score descending
            recommendations = []
            for hit in results.get("hits", {}).get("hits", []):
                quiz_id = hit["_source"].get("quiz_id")
                score = hit.get("_score", 0.0)
                recommendations.append((quiz_id, score))
                
            # Sort by score descending and limit to top_k
            recommendations.sort(key=lambda x: x[1], reverse=True)
            recommendations = recommendations[:top_k]
            
            logger.info(f"Found {len(recommendations)} quiz recommendations from {len(quiz_ids)} candidates")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend quizzes by IDs: {e}")
            return []
