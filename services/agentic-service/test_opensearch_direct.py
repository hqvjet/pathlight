"""Test OpenSearch connection và structure"""
import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3
urllib3.disable_warnings()

# Config from attachment
HOST = "127.0.0.1"
PORT = 9200
USER = "viethq1906"
PASS = "Viethq.1906"
INDEX = "pathlight-vector-v2"

auth = HTTPBasicAuth(USER, PASS)
base_url = f"https://{HOST}:{PORT}"

print("🔍 OPENSEARCH DIAGNOSTIC TEST")
print("=" * 60)

# 1. Test connection
print("\n1️⃣ Testing connection...")
try:
    resp = requests.get(f"{base_url}", auth=auth, verify=False, timeout=5)
    print(f"✅ Connected! Version: {resp.json().get('version', {}).get('number')}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# 2. Check index exists
print(f"\n2️⃣ Checking index '{INDEX}'...")
try:
    resp = requests.get(f"{base_url}/{INDEX}", auth=auth, verify=False)
    if resp.status_code == 200:
        print(f"✅ Index exists")
        # Get mapping
        mapping = resp.json()[INDEX]["mappings"]
        print(f"   Mapping keys: {list(mapping.get('properties', {}).keys())}")
    else:
        print(f"❌ Index not found: {resp.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error checking index: {e}")
    exit(1)

# 3. Count total documents
print(f"\n3️⃣ Counting documents...")
try:
    resp = requests.get(f"{base_url}/{INDEX}/_count", auth=auth, verify=False)
    count = resp.json().get("count", 0)
    print(f"✅ Total documents: {count}")
    if count == 0:
        print("⚠️  No documents indexed!")
except Exception as e:
    print(f"❌ Error counting: {e}")

# 4. Get sample documents
print(f"\n4️⃣ Fetching sample documents...")
try:
    query = {"size": 3, "query": {"match_all": {}}}
    resp = requests.post(
        f"{base_url}/{INDEX}/_search",
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps(query),
        verify=False
    )
    hits = resp.json().get("hits", {}).get("hits", [])
    print(f"✅ Retrieved {len(hits)} samples")
    
    for i, hit in enumerate(hits[:2], 1):
        source = hit.get("_source", {})
        material_id = source.get("id")
        category = source.get("category")
        num_docs = len(source.get("documents", []))
        
        print(f"\n   📄 Sample {i}:")
        print(f"      _id: {hit.get('_id')}")
        print(f"      material_id (id): {material_id} (type: {type(material_id).__name__})")
        print(f"      category: {category}")
        print(f"      documents: {num_docs}")
        
        if num_docs > 0:
            doc = source.get("documents", [])[0]
            chunks = doc.get("chunks", [])
            print(f"      first doc chunks: {len(chunks)}")
            if chunks:
                chunk = chunks[0]
                text = chunk.get("chunk_text", "")[:100]
                has_embedding = "embedding" in chunk
                emb_len = len(chunk.get("embedding", [])) if has_embedding else 0
                print(f"      sample text: {text}...")
                print(f"      has embedding: {has_embedding} (dim: {emb_len})")
                
except Exception as e:
    print(f"❌ Error fetching samples: {e}")

# 5. List all unique material IDs
print(f"\n5️⃣ Getting unique material IDs...")
try:
    agg_query = {
        "size": 0,
        "aggs": {
            "unique_ids": {
                "terms": {"field": "id", "size": 50}
            }
        }
    }
    resp = requests.post(
        f"{base_url}/{INDEX}/_search",
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps(agg_query),
        verify=False
    )
    buckets = resp.json().get("aggregations", {}).get("unique_ids", {}).get("buckets", [])
    print(f"✅ Found {len(buckets)} unique material IDs:")
    for bucket in buckets[:10]:
        print(f"      - '{bucket['key']}' (doc_count: {bucket['doc_count']})")
except Exception as e:
    print(f"❌ Error getting unique IDs: {e}")

print("\n" + "=" * 60)
print("✅ Diagnostic complete!")
