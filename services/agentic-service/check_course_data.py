"""Check what data is actually in the course from logs"""
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

# From log
course_id = "course-80eca7f5-6f24-4dbc-ba71-b1d0cf5e7951"

print(f"🔍 CHECKING DATA FOR: {course_id}")
print("=" * 70)

# Get all chunks for this course
body = {
    "size": 100,
    "query": {"term": {"id": course_id}},
    "_source": ["documents.chunks.chunk_text"]
}

resp = requests.post(
    f"{base_url}/{INDEX}/_search",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(body),
    verify=False
)

result = resp.json()
total = result.get("hits", {}).get("total", {}).get("value", 0)

print(f"\n📊 Total chunks: {total}")

if total == 0:
    print("❌ NO DATA FOUND FOR THIS COURSE!")
    print("   → This is the problem! Course was generated with empty data")
    exit(0)

print(f"\n📄 Sample chunks (first 5):")
chunks = []
for hit in result.get("hits", {}).get("hits", []):
    source = hit.get("_source", {})
    for doc in source.get("documents", []):
        for chunk in doc.get("chunks", []):
            text = chunk.get("chunk_text", "").strip()
            if text:
                chunks.append(text)

for i, text in enumerate(chunks[:5], 1):
    print(f"\n{i}. {text[:200]}...")

# Check if content is about "não bộ" (brain) or other topics
print(f"\n🔍 Content analysis:")
all_text = " ".join(chunks).lower()

keywords = {
    "não bộ": all_text.count("não bộ"),
    "brain": all_text.count("brain"),
    "neural": all_text.count("neural"),
    "giáo dục": all_text.count("giáo dục"),
    "python": all_text.count("python"),
    "programming": all_text.count("programming"),
    "table of contents": all_text.count("table of contents"),
    "mục lục": all_text.count("mục lục"),
}

print("\nKeyword frequency:")
for keyword, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"   '{keyword}': {count} times")

