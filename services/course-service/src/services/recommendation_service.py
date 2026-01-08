"""
🎯 Course Recommendation Service

Handles course recommendation requests:
1. Send RECOMMEND_COURSES message to SQS
2. Poll DynamoDB for results
3. Return recommended courses with scores
"""

import os
import time
import uuid
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from services.sqs_publisher import send_recommend_courses
from services.sim_search_dynamo_client import SimSearchDynamoClient
from src.models import Course

import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for course recommendations."""
    
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
        
        self.queue_url = os.getenv("AGENTIC_QUEUE_URL", "")
        self.region = region
        self.max_poll_attempts = 30
        self.poll_interval = 1
        
    def get_all_public_course_ids(self, db: Session) -> List[str]:
        try:
            courses = db.query(Course.id).filter(Course.publish == True).all()
            return [course.id for course in courses]
        except Exception as e:
            logger.error(f"Failed to get public course IDs: {e}")
            return []
            
    def recommend_courses(
        self, 
        user_id: str, 
        db: Session,
        topk: int = 20
    ) -> List[Dict]:
        sim_id = f"sim-course-{uuid.uuid4().hex[:8]}"
        course_ids = self.get_all_public_course_ids(db)
        
        if not course_ids:
            logger.warning("No public courses found")
            return []
            
        logger.info(f"Requesting recommendations: sim_id={sim_id}, user={user_id}, candidates={len(course_ids)}, topk={topk}")
        
        try:
            send_recommend_courses(
                queue_url=self.queue_url,
                sim_id=sim_id,
                user_id=user_id,
                course_ids=course_ids,
                topk=topk,
                region=self.region
            )
            
            for attempt in range(self.max_poll_attempts):
                result = self.dynamo_client.get_search_result(sim_id)
                
                if result is not None:
                    return self._fetch_course_details(result, db)
                    
                time.sleep(self.poll_interval)
                
            logger.warning(f"Timeout waiting for recommendations: sim_id={sim_id}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []
            
    def _fetch_course_details(
        self, 
        recommendations: List[Dict],
        db: Session
    ) -> List[Dict]:
        result = []
        
        for rec in recommendations:
            course_id = rec["id"]
            score = rec["score"]
            
            try:
                course = db.query(Course).filter(Course.course_id == course_id).first()
                if course:
                    result.append({
                        "course": course,
                        "score": score
                    })
            except Exception as e:
                logger.error(f"Failed to fetch course {course_id}: {e}")
                continue
                
        logger.info(f"Fetched {len(result)} course details from {len(recommendations)} recommendations")
        return result
