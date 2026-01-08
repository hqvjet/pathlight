"""
🎯 Quiz Recommendation Service

Handles quiz recommendation requests:
1. Send RECOMMEND_QUIZZES message to SQS
2. Poll DynamoDB for results
3. Return recommended quizzes with scores
"""

import os
import time
import uuid
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from services.sqs_publisher import send_recommend_quizzes
from services.sim_search_dynamo_client import SimSearchDynamoClient
from src.models import Quiz

import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for quiz recommendations."""
    
    def __init__(self):
        region = os.getenv("REGION", "ap-northeast-1")
        table_name = os.getenv("SIM_SEARCH_TABLE_NAME", "sim_search_table")
        access_key_id = os.getenv("ACCESS_KEY_ID")
        secret_access_key = os.getenv("SECRET_ACCESS_KEY")
        
        self.dynamo_client = SimSearchDynamoClient(
            region=region,
            table_name=table_name,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key
        )
        
        self.queue_url = os.getenv("SQS_QUEUE_URL", "")
        self.region = region
        self.max_poll_attempts = 30  # 30 seconds max wait
        self.poll_interval = 1  # 1 second between polls
        
    def get_all_public_quiz_ids(self, db: Session, exclude_user_id: Optional[str] = None) -> List[str]:
        """Get all public quiz IDs from database, optionally excluding a specific user's quizzes."""
        try:
            query = db.query(Quiz.quiz_id).filter(Quiz.publish == True)
            if exclude_user_id:
                query = query.filter(Quiz.user_id != exclude_user_id)
            quizzes = query.all()
            return [quiz.quiz_id for quiz in quizzes]
        except Exception as e:
            logger.error(f"Failed to get public quiz IDs: {e}")
            return []
            
    def recommend_quizzes(
        self, 
        user_id: str, 
        db: Session,
        topk: int = 20
    ) -> List[Dict]:
        """
        Get quiz recommendations for user.
        
        Args:
            user_id: User ID
            db: Database session
            topk: Number of recommendations
            
        Returns:
            List of recommended quizzes with details and scores:
            [
                {
                    "quiz": Quiz object,
                    "score": float
                },
                ...
            ]
        """
        # Generate unique sim_id
        sim_id = f"sim-quiz-{uuid.uuid4()}"
        
        # Get all public quizzes as candidates (excluding user's own quizzes)
        quiz_ids = self.get_all_public_quiz_ids(db, exclude_user_id=user_id)
        
        if not quiz_ids:
            logger.warning("No public quizzes found")
            return []
            
        logger.info(f"Requesting recommendations: sim_id={sim_id}, user={user_id}, candidates={len(quiz_ids)}, topk={topk}")
        
        try:
            # Send SQS message
            send_recommend_quizzes(
                queue_url=self.queue_url,
                sim_id=sim_id,
                user_id=user_id,
                quiz_ids=quiz_ids,
                topk=topk,
                region=self.region
            )
            
            # Poll DynamoDB for results
            for attempt in range(self.max_poll_attempts):
                result = self.dynamo_client.get_search_result(sim_id)
                
                if result is not None:
                    # Got results, fetch quiz details
                    recommendations = self._fetch_quiz_details(result, db)
                    # If empty recommendations, use fallback
                    if not recommendations:
                        logger.info(f"Empty recommendations for user {user_id}, using fallback")
                        return self._get_fallback_quizzes(db, topk)
                    return recommendations
                    
                # Wait before next poll
                time.sleep(self.poll_interval)
                
            # Timeout
            logger.warning(f"Timeout waiting for recommendations: sim_id={sim_id}")
            return self._get_fallback_quizzes(db, topk)
            
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return self._get_fallback_quizzes(db, topk)
            
    def _get_fallback_quizzes(self, db: Session, topk: int) -> List[Dict]:
        """Get random public quizzes as fallback when recommendations fail or return empty."""
        try:
            import random
            quizzes = db.query(Quiz).filter(Quiz.publish == True).all()
            if not quizzes:
                return []
            # Randomly sample up to topk quizzes
            sample_size = min(topk, len(quizzes))
            sampled = random.sample(quizzes, sample_size)
            return [{"quiz": quiz, "score": 0.0} for quiz in sampled]
        except Exception as e:
            logger.error(f"Failed to get fallback quizzes: {e}")
            return []
            
    def _fetch_quiz_details(
        self, 
        recommendations: List[Dict],
        db: Session
    ) -> List[Dict]:
        """
        Fetch full quiz details for recommendations.
        
        Args:
            recommendations: List of {"id": quiz_id, "score": float}
            db: Database session
            
        Returns:
            List of {"quiz": Quiz, "score": float}
        """
        result = []
        
        for rec in recommendations:
            quiz_id = rec["id"]
            score = rec["score"]
            
            try:
                quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
                if quiz:
                    result.append({
                        "quiz": quiz,
                        "score": score
                    })
            except Exception as e:
                logger.error(f"Failed to fetch quiz {quiz_id}: {e}")
                continue
                
        logger.info(f"Fetched {len(result)} quiz details from {len(recommendations)} recommendations")
        return result
