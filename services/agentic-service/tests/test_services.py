import pytest
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.mark.unit
def test_file_service_import():
    """Test that we can import file service"""
    from src.services.file_service import extract_content_with_tags
    assert extract_content_with_tags is not None
    print("✅ File service import successful")


@pytest.mark.unit
def test_text_service_import():
    """Test that we can import text service"""
    from src.services.text_service import split_into_chunks
    assert split_into_chunks is not None
    print("✅ Text service import successful")


@pytest.mark.unit
def test_text_splitting():
    """Test text splitting functionality"""
    from src.services.text_service import split_into_chunks
    
    test_text = "This is a test text. " * 50  # Create a longer text
    chunks = split_into_chunks(test_text, "test_source", max_tokens=50)
    
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all("chunk_id" in chunk for chunk in chunks)
    assert all("chunk_text" in chunk for chunk in chunks)
    assert all("chunk_source" in chunk for chunk in chunks)
    
    print(f"✅ Text splitting test passed - created {len(chunks)} chunks")


@pytest.mark.unit
def test_controller_import():
    """Test that we can import controllers"""
    from src.controllers.file_controller import FileController
    assert FileController is not None
    print("✅ File controller import successful")


@pytest.mark.integration
def test_file_controller_initialization():
    """Test file controller initialization"""
    from src.controllers.file_controller import FileController
    
    # Mock environment variables for testing
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["ACCESS_KEY_ID"] = "test-access-key"
    os.environ["SECRET_ACCESS_KEY"] = "test-secret-key"
    os.environ["S3_BUCKET_NAME"] = "test-bucket"
    
    controller = FileController()
    assert controller is not None
    print("✅ File controller initialization successful")
