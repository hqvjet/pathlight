"""Test the fixed retrieval logic"""
import sys
import os
sys.path.insert(0, '/home/hqvjet/Projects/pathlight/services/agentic-service/src')

# Set up environment
os.environ['OPENSEARCH_HOST'] = '127.0.0.1'
os.environ['OPENSEARCH_PORT'] = '9200'
os.environ['OPENSEARCH_USERNAME'] = 'viethq1906'
os.environ['OPENSEARCH_PASSWORD'] = 'Viethq.1906'
os.environ['OPENSEARCH_INDEX_NAME'] = 'pathlight-vector-v2'
os.environ['OPENAI_API_KEY'] = 'sk-proj-...'  # Add your key or use mock

print("🧪 TESTING FIXED RETRIEVAL LOGIC")
print("=" * 70)

# Import the fixed tool
from agents.base.public_tools import RetrievalTool

# Test with known material_id
test_material_id = "course-9042389f-c692-4f6f-bdc5-b530c6d8319c"
test_query = "giáo dục"

print(f"\n📌 Test Parameters:")
print(f"   Material ID: {test_material_id}")
print(f"   Query: {test_query}")
print(f"   K: 5")

try:
    tool = RetrievalTool()
    
    print("\n🔄 Running retrieval with FIXED logic...")
    result = tool._run(id=test_material_id, query=test_query, k=5)
    
    print(f"\n✅ Retrieval successful!")
    print(f"   Result length: {len(result)} chars")
    print(f"\n📄 First 300 chars of result:")
    print(result[:300])
    print("...")
    
except Exception as e:
    print(f"\n❌ Error during retrieval:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

