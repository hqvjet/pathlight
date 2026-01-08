"""
🔍 Similarity Search DynamoDB Client

Retrieves similarity search results from DynamoDB.
Used by quiz-service to get recommendation results computed by agentic-service.
"""

from typing import List, Dict, Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

import logging

logger = logging.getLogger(__name__)


class SimSearchDynamoClient:
    """DynamoDB client for reading similarity search results."""
    
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
        self.table = self.dynamodb.Table(table_name) # type: ignore[attr-defined]
        
    def get_search_result(self, sim_id: str) -> Optional[List[Dict]]:
        """
        Get similarity search result from DynamoDB.
        
        Args:
            sim_id: Search ID
            
        Returns:
            List of {"id": item_id, "score": sim_score} or None if not found
            
        DynamoDB format:
        {
            "sim_id": "search-123",
            "ids": ["quiz-1", "quiz-2", "quiz-3"],
            "scores": [0.95, 0.87, 0.73]
        }
        """
        try:
            response = self.table.get_item(Key={"sim_id": sim_id})
            
            if "Item" not in response:
                logger.warning(f"Search result not found: {sim_id}")
                return None
                
            item = response["Item"]
            ids = item.get("ids", [])
            scores = item.get("scores", [])
            
            # Convert to list of dicts
            result = []
            for item_id, score in zip(ids, scores):
                result.append({
                    "id": item_id,
                    "score": float(score)  # Convert Decimal to float
                })
                
            logger.info(f"Retrieved search result: {sim_id} ({len(result)} items)")
            return result
            
        except ClientError as e:
            logger.error(f"DynamoDB error getting search result {sim_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get search result {sim_id}: {e}")
            return None
