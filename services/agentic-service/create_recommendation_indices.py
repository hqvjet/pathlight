#!/usr/bin/env python3
"""Create OpenSearch indices for recommendation system.

Creates:
- pathlight-course-vectors: Course embeddings
- pathlight-quiz-vectors: Quiz embeddings
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from infrastructure.clients import clients
from infrastructure.opensearch_mappings import COURSE_VECTOR_MAPPING, QUIZ_VECTOR_MAPPING
from constant import COURSE_VECTOR_INDEX, QUIZ_VECTOR_INDEX

def create_indices():
    """Create recommendation system indices in OpenSearch."""
    client = clients.opensearch
    
    if not client or not client.is_available():
        print("❌ OpenSearch client not available")
        sys.exit(1)
        
    print("✅ OpenSearch client connected")
    
    # Get the actual OpenSearch client
    os = client.client
    
    # Create course vector index
    try:
        if os.indices.exists(index=COURSE_VECTOR_INDEX):
            print(f"⚠️  Index {COURSE_VECTOR_INDEX} already exists")
            response = input(f"Delete and recreate? (y/n): ")
            if response.lower() == 'y':
                os.indices.delete(index=COURSE_VECTOR_INDEX)
                print(f"🗑️  Deleted {COURSE_VECTOR_INDEX}")
            else:
                print(f"⏭️  Skipping {COURSE_VECTOR_INDEX}")
                # Continue to quiz index
                
        if not os.indices.exists(index=COURSE_VECTOR_INDEX):
            os.indices.create(
                index=COURSE_VECTOR_INDEX,
                body=COURSE_VECTOR_MAPPING
            )
            print(f"✅ Created index: {COURSE_VECTOR_INDEX}")
        
    except Exception as e:
        print(f"❌ Failed to create {COURSE_VECTOR_INDEX}: {e}")
        sys.exit(1)
        
    # Create quiz vector index
    try:
        if os.indices.exists(index=QUIZ_VECTOR_INDEX):
            print(f"⚠️  Index {QUIZ_VECTOR_INDEX} already exists")
            response = input(f"Delete and recreate? (y/n): ")
            if response.lower() == 'y':
                os.indices.delete(index=QUIZ_VECTOR_INDEX)
                print(f"🗑️  Deleted {QUIZ_VECTOR_INDEX}")
            else:
                print(f"⏭️  Skipping {QUIZ_VECTOR_INDEX}")
                print("\n🎉 Done!")
                return
                
        if not os.indices.exists(index=QUIZ_VECTOR_INDEX):
            os.indices.create(
                index=QUIZ_VECTOR_INDEX,
                body=QUIZ_VECTOR_MAPPING
            )
            print(f"✅ Created index: {QUIZ_VECTOR_INDEX}")
        
    except Exception as e:
        print(f"❌ Failed to create {QUIZ_VECTOR_INDEX}: {e}")
        sys.exit(1)
        
    print("\n🎉 All recommendation indices created successfully!")

if __name__ == "__main__":
    create_indices()
