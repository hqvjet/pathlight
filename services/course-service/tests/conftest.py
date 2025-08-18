import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure imports work in CI regardless of cwd
SERVICE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = SERVICE_ROOT / "src"
for p in (str(SRC_DIR), str(SERVICE_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Ensure DB setup is skipped for tests
os.environ.setdefault("COURSE_SKIP_DB_SETUP", "true")
os.environ.setdefault("COURSE_SERVICE_SKIP_DB", "true")

from src.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)
