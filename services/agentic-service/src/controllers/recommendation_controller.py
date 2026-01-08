"""Recommendation controller for course/quiz suggestions.

Exposes endpoints for:
1. Computing user profile vector
2. Getting course recommendations
3. Getting quiz recommendations
"""

from typing import List, Dict, Optional

from core.logging import setup_logger
from core.exceptions import InternalServerError
from services.recommendation_service import RecommendationService

logger = setup_logger(__name__)


class RecommendationController:
    def __init__(self):
        self.rec_service = RecommendationService()
        
    def get_user_profile_vector(self, user_id: str) -> Optional[List[float]]:
        """Compute and return user profile vector.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile vector or None if user has no content
            
        Raises:
            InternalServerError: If computation fails
        """
        try:
            vector = self.rec_service.compute_user_profile_vector(user_id)
            if vector is None:
                logger.warning(f"User {user_id} has no content - cannot compute profile")
                return None
            return vector
        except Exception as e:
            logger.error(f"Failed to compute user profile vector: {e}")
            raise InternalServerError(f"Failed to compute user profile: {str(e)}")
            
    def recommend_courses(
        self,
        user_id: str,
        top_k: int = 10,
        level: Optional[str] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None
    ) -> List[Dict]:
        """Get course recommendations for user.
        
        Args:
            user_id: User identifier
            top_k: Number of recommendations
            level: Filter by difficulty level (easy, medium, hard)
            min_duration: Minimum duration in minutes
            max_duration: Maximum duration in minutes
            
        Returns:
            List of recommended courses with metadata
            
        Raises:
            InternalServerError: If recommendation fails
        """
        try:
            # Compute user profile vector
            user_vector = self.get_user_profile_vector(user_id)
            if user_vector is None:
                logger.info(f"No profile for user {user_id} - returning empty recommendations")
                return []
                
            # Build filters
            filters = {"publish": True}  # Only public courses
            if level:
                filters["level"] = level
                
            # Get recommendations
            recommendations = self.rec_service.recommend_courses(
                user_vector=user_vector,
                top_k=top_k,
                filters=filters
            )
            
            # Apply duration filters (post-processing since range queries need different syntax)
            if min_duration is not None or max_duration is not None:
                filtered = []
                for rec in recommendations:
                    duration = rec.get("duration", 0)
                    if min_duration and duration < min_duration:
                        continue
                    if max_duration and duration > max_duration:
                        continue
                    filtered.append(rec)
                recommendations = filtered
                
            logger.info(f"Recommended {len(recommendations)} courses for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend courses: {e}")
            raise InternalServerError(f"Failed to recommend courses: {str(e)}")
            
    def recommend_quizzes(
        self,
        user_id: str,
        top_k: int = 10,
        level: Optional[str] = None,
        min_questions: Optional[int] = None,
        max_questions: Optional[int] = None
    ) -> List[Dict]:
        """Get quiz recommendations for user.
        
        Args:
            user_id: User identifier
            top_k: Number of recommendations
            level: Filter by difficulty level (easy, medium, hard)
            min_questions: Minimum number of questions
            max_questions: Maximum number of questions
            
        Returns:
            List of recommended quizzes with metadata
            
        Raises:
            InternalServerError: If recommendation fails
        """
        try:
            # Compute user profile vector
            user_vector = self.get_user_profile_vector(user_id)
            if user_vector is None:
                logger.info(f"No profile for user {user_id} - returning empty recommendations")
                return []
                
            # Build filters
            filters = {"publish": True}  # Only public quizzes
            if level:
                filters["level"] = level
                
            # Get recommendations
            recommendations = self.rec_service.recommend_quizzes(
                user_vector=user_vector,
                top_k=top_k,
                filters=filters
            )
            
            # Apply num_questions filters (post-processing)
            if min_questions is not None or max_questions is not None:
                filtered = []
                for rec in recommendations:
                    num_q = rec.get("num_questions", 0)
                    if min_questions and num_q < min_questions:
                        continue
                    if max_questions and num_q > max_questions:
                        continue
                    filtered.append(rec)
                recommendations = filtered
                
            logger.info(f"Recommended {len(recommendations)} quizzes for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend quizzes: {e}")
            raise InternalServerError(f"Failed to recommend quizzes: {str(e)}")
