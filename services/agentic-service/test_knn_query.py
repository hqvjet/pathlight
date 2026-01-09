"""Test KNN query với filter để tìm root cause"""
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

print("🧪 TESTING KNN QUERY WITH FILTER")
print("=" * 70)

# Pick a known material_id from diagnostic
test_material_id = "course-9042389f-c692-4f6f-bdc5-b530c6d8319c"
print(f"\n📌 Testing with material_id: {test_material_id}")

# First, verify filter alone works
print("\n1️⃣ Test FILTER alone (no KNN)...")
filter_only_query = {
    "size": 5,
    "query": {
        "term": {"id": test_material_id}
    }
}

resp = requests.post(
    f"{base_url}/{INDEX}/_search",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(filter_only_query),
    verify=False
)

result = resp.json()
filter_hits = result.get("hits", {}).get("total", {}).get("value", 0)
print(f"   ✅ Filter alone found: {filter_hits} chunks")

if filter_hits > 0:
    sample = result["hits"]["hits"][0]["_source"]
    print(f"   Sample text: {sample['documents'][0]['chunks'][0]['chunk_text'][:80]}...")
else:
    print("   ❌ No results with filter!")
    exit(1)

# Now test KNN query (the WRONG way - current implementation)
print("\n2️⃣ Test WRONG KNN query (current implementation)...")
wrong_knn_query = {
    "size": 5,
    "query": {
        "bool": {
            "filter": {
                "term": {"id": test_material_id}
            },
            "must": {
                "knn": {
                    "documents.chunks.embedding": {
                        "vector": [0.1] * 1536,  # Dummy vector
                        "k": 10000
                    }
                }
            }
        }
    }
}

try:
    resp = requests.post(
        f"{base_url}/{INDEX}/_search",
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps(wrong_knn_query),
        verify=False
    )
    result = resp.json()
    
    if "error" in result:
        print(f"   ❌ Query failed: {result['error']['type']}")
        print(f"   Reason: {result['error']['reason']}")
    else:
        wrong_hits = result.get("hits", {}).get("total", {}).get("value", 0)
        print(f"   Results: {wrong_hits} chunks")
        if wrong_hits == 0:
            print(f"   ⚠️ KNN inside bool.must returned 0 results!")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test CORRECT KNN query (script query approach)
print("\n3️⃣ Test CORRECT KNN query (script_score with filter)...")
correct_knn_query = {
    "size": 5,
    "query": {
        "script_score": {
            "query": {
                "term": {"id": test_material_id}
            },
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'documents.chunks.embedding') + 1.0",
                "params": {
                    "query_vector": [0.1] * 1536
                }
            }
        }
    }
}

try:
    resp = requests.post(
        f"{base_url}/{INDEX}/_search",
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps(correct_knn_query),
        verify=False
    )
    result = resp.json()
    
    if "error" in result:
        print(f"   ❌ Query failed: {result['error']['type']}")
        print(f"   Reason: {result['error']['reason']}")
    else:
        correct_hits = result.get("hits", {}).get("total", {}).get("value", 0)
        print(f"   ✅ Results: {correct_hits} chunks")
        if correct_hits > 0:
            print(f"   First hit score: {result['hits']['hits'][0]['_score']:.4f}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test native KNN search (OpenSearch native KNN)
print("\n4️⃣ Test NATIVE KNN (OpenSearch 2.x native KNN)...")
native_knn_query = {
    "size": 5,
    "query": {
        "knn": {
            "documents.chunks.embedding": {
                "vector": [0.1] * 1536,
                "k": 5,
                "filter": {
                    "term": {"id": test_material_id}
                }
            }
        }
    }
}

try:
    resp = requests.post(
        f"{base_url}/{INDEX}/_search",
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps(native_knn_query),
        verify=False
    )
    result = resp.json()
    
    if "error" in result:
        print(f"   ❌ Query failed: {result['error']['type']}")
        print(f"   Reason: {result['error']['reason']}")
    else:
        native_hits = result.get("hits", {}).get("total", {}).get("value", 0)
        print(f"   ✅ Results: {native_hits} chunks")
        if native_hits > 0:
            print(f"   First hit score: {result['hits']['hits'][0]['_score']:.4f}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("📊 SUMMARY:")
print(f"   Filter alone: {filter_hits} hits ✅")
print("   Wrong KNN (bool.must): Check above")
print("   Correct script_score: Check above")
print("   Native KNN: Check above")
