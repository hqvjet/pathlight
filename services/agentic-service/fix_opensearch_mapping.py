"""
Script để fix mapping của OpenSearch index cho KNN vector search
"""
import requests
import json
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
OPENSEARCH_HOST = "127.0.0.1"
OPENSEARCH_PORT = 9200
OPENSEARCH_USERNAME = "viethq1906"
OPENSEARCH_PASSWORD = "Viethq.1906"
OLD_INDEX_NAME = "pathlight-vector"
NEW_INDEX_NAME = "pathlight-vector-v2"
OPENSEARCH_URL = f"https://{OPENSEARCH_HOST}:{OPENSEARCH_PORT}"

auth = HTTPBasicAuth(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD)

def create_new_index_with_correct_mapping():
    """Tạo index mới với mapping đúng cho KNN vector search"""
    
    # Mapping đúng với knn_vector type
    mapping = {
        "settings": {
            "index": {
                "knn": True,  # Enable KNN
                "knn.algo_param.ef_search": 100
            }
        },
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword"  # Đổi thành keyword để filter hiệu quả hơn
                },
                "category": {
                    "type": "long"
                },
                "documents": {
                    "properties": {
                        "document_id": {
                            "type": "long"
                        },
                        "document_source": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "chunks": {
                            "properties": {
                                "chunk_id": {
                                    "type": "long"
                                },
                                "chunk_text": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "embedding": {
                                    "type": "knn_vector",  # Đây là điểm quan trọng!
                                    "dimension": 1536,  # OpenAI text-embedding-3-small dimension
                                    "method": {
                                        "name": "hnsw",
                                        "space_type": "cosinesimil",
                                        "engine": "nmslib",
                                        "parameters": {
                                            "ef_construction": 128,
                                            "m": 24
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Xóa index mới nếu đã tồn tại
    print(f"Xóa index cũ {NEW_INDEX_NAME} nếu tồn tại...")
    response = requests.delete(
        f"{OPENSEARCH_URL}/{NEW_INDEX_NAME}",
        auth=auth,
        verify=False
    )
    print(f"Kết quả xóa: {response.status_code}")
    
    # Tạo index mới
    print(f"\nTạo index mới {NEW_INDEX_NAME} với mapping đúng...")
    response = requests.put(
        f"{OPENSEARCH_URL}/{NEW_INDEX_NAME}",
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps(mapping),
        verify=False
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Tạo index thành công!")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ Lỗi khi tạo index: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def reindex_data():
    """Reindex dữ liệu từ index cũ sang index mới"""
    print(f"\nBắt đầu reindex từ {OLD_INDEX_NAME} sang {NEW_INDEX_NAME}...")
    
    reindex_body = {
        "source": {
            "index": OLD_INDEX_NAME
        },
        "dest": {
            "index": NEW_INDEX_NAME
        }
    }
    
    response = requests.post(
        f"{OPENSEARCH_URL}/_reindex",
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps(reindex_body),
        verify=False,
        timeout=300  # 5 phút timeout
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Reindex thành công!")
        print(f"   - Tổng số documents: {result.get('total', 0)}")
        print(f"   - Đã index: {result.get('created', 0)}")
        print(f"   - Thời gian: {result.get('took', 0)}ms")
        return True
    else:
        print(f"❌ Lỗi khi reindex: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def create_alias():
    """Tạo alias để trỏ từ tên cũ sang index mới"""
    print(f"\nTạo alias {OLD_INDEX_NAME} trỏ đến {NEW_INDEX_NAME}...")
    
    # Xóa alias cũ nếu có
    requests.delete(
        f"{OPENSEARCH_URL}/{OLD_INDEX_NAME}/_alias/{OLD_INDEX_NAME}",
        auth=auth,
        verify=False
    )
    
    # Tạo alias mới
    response = requests.post(
        f"{OPENSEARCH_URL}/_aliases",
        auth=auth,
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "actions": [
                {
                    "add": {
                        "index": NEW_INDEX_NAME,
                        "alias": OLD_INDEX_NAME
                    }
                }
            ]
        }),
        verify=False
    )
    
    if response.status_code == 200:
        print(f"✅ Tạo alias thành công!")
        return True
    else:
        print(f"❌ Lỗi khi tạo alias: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def verify_mapping():
    """Kiểm tra mapping của index mới"""
    print(f"\n📋 Kiểm tra mapping của index mới...")
    response = requests.get(
        f"{OPENSEARCH_URL}/{NEW_INDEX_NAME}/_mapping",
        auth=auth,
        verify=False
    )
    
    if response.status_code == 200:
        mapping = response.json()
        embedding_type = mapping[NEW_INDEX_NAME]["mappings"]["properties"]["documents"]["properties"]["chunks"]["properties"]["embedding"]
        print(f"✅ Embedding field type: {embedding_type.get('type')}")
        print(f"   Dimension: {embedding_type.get('dimension')}")
        print(f"   Method: {embedding_type.get('method', {}).get('name')}")
        return True
    else:
        print(f"❌ Lỗi khi kiểm tra mapping")
        return False

def main():
    print("="*60)
    print("🔧 OpenSearch Mapping Fix Script")
    print("="*60)
    
    # Bước 1: Tạo index mới với mapping đúng
    if not create_new_index_with_correct_mapping():
        print("\n❌ Không thể tạo index mới. Dừng lại.")
        return
    
    # Bước 2: Reindex dữ liệu
    print("\n" + "="*60)
    if not reindex_data():
        print("\n⚠️  Reindex thất bại, nhưng index mới đã được tạo.")
        print("    Bạn có thể reindex thủ công sau.")
    
    # Bước 3: Tạo alias (optional - để giữ tên cũ)
    print("\n" + "="*60)
    print("\n⚠️  Lưu ý: Bước này sẽ tạo alias để code cũ vẫn hoạt động.")
    print("    Hoặc bạn có thể cập nhật .env để dùng index mới.")
    choice = input("\nBạn có muốn tạo alias không? (y/n): ")
    
    if choice.lower() == 'y':
        create_alias()
    else:
        print(f"\n💡 Hãy cập nhật .env:")
        print(f"   OPENSEARCH_INDEX_NAME={NEW_INDEX_NAME}")
    
    # Bước 4: Verify
    print("\n" + "="*60)
    verify_mapping()
    
    print("\n" + "="*60)
    print("✅ Hoàn thành!")
    print("="*60)
    print("\n📝 Các bước tiếp theo:")
    print("   1. Cập nhật .env với index mới (nếu chưa tạo alias)")
    print("   2. Test lại application")
    print("   3. Nếu mọi thứ OK, có thể xóa index cũ:")
    print(f"      curl -k -u {OPENSEARCH_USERNAME}:*** -X DELETE https://{OPENSEARCH_HOST}:{OPENSEARCH_PORT}/{OLD_INDEX_NAME}")

if __name__ == "__main__":
    main()
