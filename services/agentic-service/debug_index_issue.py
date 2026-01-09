"""Debug why indexed data is not found"""
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

course_id = "course-80eca7f5-6f24-4dbc-ba71-b1d0cf5e7951"

print("🔍 DEBUGGING INDEX ISSUE")
print("=" * 70)

# 1. Check if this exact string exists in ANY field
print(f"\n1️⃣ Search for '{course_id}' in ANY field...")
body = {
    "size": 5,
    "query": {
        "query_string": {
            "query": f'"{course_id}"',
            "fields": ["*"]
        }
    }
}

resp = requests.post(
    f"{base_url}/{INDEX}/_search",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(body),
    verify=False
)

result = resp.json()
hits = result.get("hits", {}).get("total", {}).get("value", 0)
print(f"   Found: {hits} documents")

if hits > 0:
    print("   Sample _id:", result["hits"]["hits"][0]["_id"])
    print("   Sample id field:", result["hits"]["hits"][0]["_source"].get("id"))

# 2. Try with match instead of term
print(f"\n2️⃣ Try with 'match' query...")
body = {
    "size": 5,
    "query": {
        "match": {"id": course_id}
    }
}

resp = requests.post(
    f"{base_url}/{INDEX}/_search",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(body),
    verify=False
)

result = resp.json()
hits = result.get("hits", {}).get("total", {}).get("value", 0)
print(f"   Found: {hits} documents")

# 3. Try partial match
print(f"\n3️⃣ Try partial match (first 20 chars)...")
partial_id = course_id[:20]
body = {
    "size": 5,
    "query": {
        "wildcard": {"id": f"{partial_id}*"}
    }
}

resp = requests.post(
    f"{base_url}/{INDEX}/_search",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(body),
    verify=False
)

result = resp.json()
hits = result.get("hits", {}).get("total", {}).get("value", 0)
print(f"   Found: {hits} documents")

# 4. Check recent documents
print(f"\n4️⃣ Get 5 most recent documents...")
body = {
    "size": 5,
    "sort": [{"_id": {"order": "desc"}}],
    "query": {"match_all": {}}
}

resp = requests.post(
    f"{base_url}/{INDEX}/_search",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(body),
    verify=False
)

result = resp.json()
print(f"   Recent document IDs:")
for hit in result.get("hits", {}).get("hits", []):
    doc_id = hit["_source"].get("id")
    print(f"      - {doc_id}")

# 5. Check if using composite _id affects filtering
print(f"\n5️⃣ Search by _id (composite ID)...")
composite_id = f"{course_id}:1:1"
body = {
    "query": {
        "ids": {"values": [composite_id]}
    }
}

resp = requests.post(
    f"{base_url}/{INDEX}/_search",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(body),
    verify=False
)

result = resp.json()
hits = result.get("hits", {}).get("total", {}).get("value", 0)
print(f"   Found by composite _id: {hits}")

if hits > 0:
    print(f"   ✅ Document exists with _id={composite_id}")
    print(f"   But 'id' field value:", result["hits"]["hits"][0]["_source"].get("id"))

