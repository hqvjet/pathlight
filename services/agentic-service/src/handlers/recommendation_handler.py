"""
🎯 Recommendation Handler

Handles similarity search requests from course/quiz service.
Computes recommendations and stores results in DynamoDB.
"""

from typing import Dict, Any

from core.logging import setup_logger
from services.recommendation_service import RecommendationService
from infrastructure.aws.sim_search_dynamo_client import SimSearchDynamoClient
from config import config


logger = setup_logger(__name__)


class RecommendationHandler:
    """Handler for similarity search requests."""
    
    def __init__(self):
        self.rec_service = RecommendationService()
        self.sim_search_client = SimSearchDynamoClient(
            region=config.REGION,
            table_name=config.SIM_SEARCH_TABLE_NAME,
            access_key_id=config.ACCESS_KEY_ID,
            secret_access_key=config.SECRET_ACCESS_KEY
        )
        
    def handle_recommend_courses(self, payload: Dict[str, Any]) -> None:
        """
        Handle RECOMMEND_COURSES message.
        
        Payload:
        {
            "sim_id": "search-123",
            "user_id": "user-456",
            "topk": 10,
            "course_ids": ["course-1", "course-2", ...]
        }
        
        Result stored in DynamoDB sim_search_table:
        {
            "sim_id": "search-123",
            "result": [
                ["course-1", 0.95],
                ["course-2", 0.87],
                ...
            ]
        }
        """
        sim_id = payload.get("sim_id")
        user_id = payload.get("user_id")
        topk = payload.get("topk", 10)
        course_ids = payload.get("course_ids", [])
        
        logger.info(f"Recommending courses: sim_id={sim_id}, user={user_id}, topk={topk}, candidates={len(course_ids)}")
        
        try:
            # Compute user profile vector
            user_vector = self.rec_service.compute_user_profile_vector(user_id)
            
            if user_vector is None:
                logger.warning(f"No profile vector for user {user_id} - returning empty recommendations")
                # Still save empty result
                self.sim_search_client.save_search_result(sim_id, [])
                return
                
            # Get recommendations filtered by course_ids
            recommendations = self.rec_service.recommend_courses_by_ids(
                user_vector=user_vector,
                course_ids=course_ids,
                top_k=topk
            )
            
            # Save to DynamoDB
            self.sim_search_client.save_search_result(sim_id, recommendations)
            
            logger.info(f"Saved {len(recommendations)} course recommendations for sim_id={sim_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle recommend_courses for sim_id={sim_id}: {e}")
            # Save empty result on error so course service doesn't wait forever
            self.sim_search_client.save_search_result(sim_id, [])
            raise
            
    def handle_recommend_quizzes(self, payload: Dict[str, Any]) -> None:
        """
        Handle RECOMMEND_QUIZZES message.
        
        Payload:
        {
            "sim_id": "search-789",
            "user_id": "user-456",
            "topk": 5,
            "quiz_ids": ["quiz-1", "quiz-2", ...]
        }
        
        Result stored in DynamoDB sim_search_table:
        {
            "sim_id": "search-789",
            "result": [
                ["quiz-1", 0.93],
                ["quiz-2", 0.81],
                ...
            ]
        }
        """
        sim_id = payload.get("sim_id")
        user_id = payload.get("user_id")
        topk = payload.get("topk", 10)
        quiz_ids = payload.get("quiz_ids", [])
        
        logger.info(f"Recommending quizzes: sim_id={sim_id}, user={user_id}, topk={topk}, candidates={len(quiz_ids)}")
        
        try:
            # Compute user profile vector
            user_vector = self.rec_service.compute_user_profile_vector(user_id)
            
            if user_vector is None:
                logger.warning(f"No profile vector for user {user_id} - returning empty recommendations")
                # Still save empty result
                self.sim_search_client.save_search_result(sim_id, [])
                return
                
            # Get recommendations filtered by quiz_ids
            recommendations = self.rec_service.recommend_quizzes_by_ids(
                user_vector=user_vector,
                quiz_ids=quiz_ids,
                top_k=topk
            )
            
            # Save to DynamoDB
            self.sim_search_client.save_search_result(sim_id, recommendations)
            
            logger.info(f"Saved {len(recommendations)} quiz recommendations for sim_id={sim_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle recommend_quizzes for sim_id={sim_id}: {e}")
            # Save empty result on error so quiz service doesn't wait forever
            self.sim_search_client.save_search_result(sim_id, [])
            raise
