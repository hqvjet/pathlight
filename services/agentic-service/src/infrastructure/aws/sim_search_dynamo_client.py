"""
🔍 Similarity Search DynamoDB Client

Manages similarity search results storage in DynamoDB.
Course/Quiz service triggers search via SQS, results stored here with sim_id as key.
"""

from typing import List, Tuple, Optional, Dict
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

from core.logging import setup_logger


logger = setup_logger(__name__)


class SimSearchDynamoClient:
    """DynamoDB client for similarity search results."""
    
    def __init__(self, region: str, table_name: str, access_key_id: Optional[str] = None, 
                 secret_access_key: Optional[str] = None):
        """
        Initialize similarity search DynamoDB client.
        
        Args:
            region: AWS region
            table_name: DynamoDB table name (sim_search_table)
            access_key_id: AWS access key ID (optional)
            secret_access_key: AWS secret access key (optional)
        """
        self.table_name = table_name
        
        # Initialize DynamoDB resource
        kwargs = {"region_name": region}
        if access_key_id and secret_access_key:
            kwargs["aws_access_key_id"] = access_key_id
            kwargs["aws_secret_access_key"] = secret_access_key
            
        self.dynamodb = boto3.resource('dynamodb', **kwargs)
        self.table = self.dynamodb.Table(table_name)
        
    def save_search_result(
        self, 
        sim_id: str, 
        result: List[Tuple[str, float]]
    ) -> None:
        """
        Save similarity search result to DynamoDB.
        
        Args:
            sim_id: Unique search ID (provided by course/quiz service)
            result: List of (item_id, sim_score) tuples, sorted by score descending
            
        Format in DynamoDB:
        {
            "sim_id": "search-123",
            "ids": ["course-1", "course-2", "course-3"],
            "scores": [0.95, 0.87, 0.73]
        }
        """
        try:
            # Split into 2 parallel arrays - cleaner DynamoDB format
            ids = [item_id for item_id, _ in result]
            scores = [Decimal(str(score)) for _, score in result]
            
            item = {
                "sim_id": sim_id,
                "ids": ids,
                "scores": scores
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Saved similarity search result: {sim_id} ({len(result)} items)")
            
        except Exception as e:
            logger.error(f"Failed to save search result {sim_id}: {e}")
            raise
            
    def get_search_result(self, sim_id: str) -> Optional[List[Dict]]:
        """
        Get similarity search result from DynamoDB.
        
        Args:
            sim_id: Search ID
            
        Returns:
            List of {"id": item_id, "score": sim_score} or None if not found
        """
        try:
            response = self.table.get_item(Key={"sim_id": sim_id})
            
            if "Item" not in response:
                logger.warning(f"Search result not found: {sim_id}")
                return None
                
            item = response["Item"]
            ids = item.get("ids", [])
            scores = item.get("scores", [])
            
            # Zip parallel arrays back into list of dicts
            result = [
                {
                    "id": item_id,
                    "score": float(score)
                }
                for item_id, score in zip(ids, scores)
            ]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get search result {sim_id}: {e}")
            raise
