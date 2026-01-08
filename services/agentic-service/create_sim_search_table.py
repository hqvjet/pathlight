#!/usr/bin/env python3
"""Create DynamoDB table for similarity search results.

Table: sim_search_table
- sim_id (String, HASH key): Unique search ID from course/quiz service
- result (List): [[item_id, sim_score], ...] sorted by score descending
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

import boto3
from config import config

def create_sim_search_table():
    """Create sim_search_table in DynamoDB."""
    
    # Use local DynamoDB for testing
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=config.REGION,
        endpoint_url=os.getenv('DYNAMODB_ENDPOINT', None),  # Use local if set
        aws_access_key_id=config.ACCESS_KEY_ID or None,
        aws_secret_access_key=config.SECRET_ACCESS_KEY or None
    )
    
    table_name = config.SIM_SEARCH_TABLE_NAME
    
    print(f"Creating DynamoDB table: {table_name}...")
    
    try:
        # Check if table exists
        existing_tables = list(dynamodb.tables.all())
        if any(t.name == table_name for t in existing_tables):
            print(f"⚠️  Table {table_name} already exists")
            response = input("Delete and recreate? (y/n): ")
            if response.lower() == 'y':
                table = dynamodb.Table(table_name)
                table.delete()
                table.wait_until_not_exists()
                print(f"🗑️  Deleted {table_name}")
            else:
                print(f"⏭️  Skipping table creation")
                return
        
        # Create table
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'sim_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'sim_id',
                    'AttributeType': 'S'  # String
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand pricing
        )
        
        # Wait for table to be created
        print("Waiting for table to be created...")
        table.wait_until_exists()
        
        print(f"✅ Created DynamoDB table: {table_name}")
        print(f"   - Partition key: sim_id (String)")
        print(f"   - Billing mode: PAY_PER_REQUEST")
        
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_sim_search_table()
    print("\n🎉 sim_search_table ready for use!")
