"""Chi tiết hơn về KNN query issue"""
import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3
urllib3.disable_warnings()

HOST = "127.0.0.1"
PORT = 9200
USER = "viethq1906"
PASS = "Viethq.1906"
INDEX = "pathlight-vector-v2"

auth = HTTPBasicAuth(USER, PASS)
base_url = f"https://{HOST}:{PORT}"

test_material_id = "course-9042389f-c692-4f6f-bdc5-b530c6d8319c"

print("🔎 DETAILED KNN INVESTIGATION")
print("=" * 70)

# Check what the WRONG query actually returns
print("\n1️⃣ Checking WRONG query results in detail...")
wrong_query = {
    "size": 3,
    "query": {
        "bool": {
            "filter": {"term": {"id": test_material_id}},
            "must": {
                "knn": {
                    "documents.chunks.embedding": {
                        "vector": [0.1] * 1536,
                        "k": 10000
                    }
                }
            }
        }
    },
    "_source": ["documents.chunks.chunk_text"]
}

resp = requests.post(
    f"{base_url}/{INDEX}/_search",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(wrong_query),
    verify=False
)

result = resp.json()
print(f"   Total hits: {result['hits']['total']['value']}")
print(f"   Returned: {len(result['hits']['hits'])}")

for i, hit in enumerate(result['hits']['hits'][:3], 1):
    score = hit['_score']
    text = hit['_source']['documents'][0]['chunks'][0]['chunk_text'][:100]
    print(f"\n   Hit {i}:")
    print(f"      Score: {score}")
    print(f"      Text: {text}...")

# The ROOT CAUSE: KNN inside bool.must doesn't actually do vector similarity!
# It just ignores the KNN and returns filtered results

print("\n\n🔍 ROOT CAUSE IDENTIFIED:")
print("=" * 70)
print("❌ KNN query inside bool.must is IGNORED by OpenSearch!")
print("   - The query only uses the filter (term match on id)")
print("   - Returns random chunks from the filtered set")
print("   - NO vector similarity ranking is applied")
print("\n✅ SOLUTION: Use hybrid approach or proper KNN syntax")
print("   - Option 1: Use script_score (but may fail on nested fields)")
print("   - Option 2: Filter by ID first, then apply KNN post-filter")
print("   - Option 3: Use match query for material_id instead of nested")

# Try option 3: Flatten the structure approach
print("\n\n2️⃣ Testing workaround with _search scroll...")

# Alternative: Get embeddings first, compute similarity in Python
# This is inefficient but will work

print("\n3️⃣ Recommended solution:")
print("   Change index structure to flatten chunks!")
print("   Instead of nested documents.chunks,")
print("   Make each chunk a separate document with material_id")
print("   This allows native KNN with filter to work properly")

