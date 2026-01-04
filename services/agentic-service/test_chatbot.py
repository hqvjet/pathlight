"""
Example test for chatbot Q&A workflow

Demonstrates how to send chatbot questions via SQS.
"""

import json
from datetime import datetime

# Example SQS message for chatbot question
chatbot_message = {
    "type": "CHATBOT_QUESTION",
    "correlation_id": "test-chatbot-001",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "payload": {
        "chat_id": "chat-12345",
        "message": "What is the main topic of this lesson?",
        "lesson_id": "course-dd8aa8e2-aa57-46e5-9306-89590f62b67d-L2",
        "course_id": "course-dd8aa8e2-aa57-46e5-9306-89590f62b67d",  # This is used as material_id in OpenSearch
        "user_id": "b3aa1376-0c62-4b99-8948-38c6e478cf8a"
    }
}

print("Example SQS Message for Chatbot Question:")
print("=" * 60)
print(json.dumps(chatbot_message, indent=2))
print("=" * 60)

# Workflow explanation
print("\nWorkflow:")
print("1. SQS receives CHATBOT_QUESTION message")
print("2. Handler creates DynamoDB record with status='processing'")
print("3. Service retrieves relevant context from OpenSearch using course_id")
print("   - Embeds user question using OpenAI")
print("   - Performs KNN vector search filtered by course_id")
print("   - Returns top 5 most relevant chunks")
print("4. Service generates answer using gpt-4o-mini with retrieved context")
print("5. Handler updates DynamoDB record with status='done' and response")
print("\nDynamoDB Record Structure:")
print("- PK: chat_id")
print("- Fields: message, lesson_id, course_id, user_id, status, response, error_message, context_chunks, created_at, updated_at")
print("- Status values: 'processing' | 'done' | 'error'")

print("\n" + "=" * 60)
print("Testing locally:")
print("=" * 60)
print("""
# 1. Ensure OpenSearch and DynamoDB are configured
export OPENSEARCH_HOST="your-opensearch-host"
export OPENSEARCH_USERNAME="your-username"
export OPENSEARCH_PASSWORD="your-password"
export CHATBOT_DDB_TABLE_NAME="chatbot_table"
export DDB_AUTO_CREATE_TABLE="true"  # For local testing

# 2. Ensure course materials are vectorized in OpenSearch
# The course_id in the message must match the material_id used during vectorization

# 3. Test the handler
python -c "
from handlers.sqs_handler import process_sqs_event
from contracts.sqs_contracts import SQSEvent, SQSRecord
import json

event = SQSEvent(Records=[
    SQSRecord(
        messageId='test-msg-001',
        body=json.dumps({
            'type': 'CHATBOT_QUESTION',
            'correlation_id': 'test-001',
            'timestamp': '2024-01-05T10:00:00Z',
            'payload': {
                'chat_id': 'chat-test-001',
                'message': 'What is this lesson about?',
                'lesson_id': 'lesson-001',
                'course_id': 'your-course-id',  # Must exist in OpenSearch
                'user_id': 'user-001'
            }
        })
    )
])

result = process_sqs_event(event)
print(f'Failures: {len(result.batchItemFailures)}')
"
""")
