import os
import pytest
from fastapi.testclient import TestClient

# Ensure DB setup is skipped for tests
os.environ.setdefault("COURSE_SKIP_DB_SETUP", "true")

from src.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)
