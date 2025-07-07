import pytest
import asyncio
import logging
import warnings
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import tempfile

# Configure logging to suppress APScheduler shutdown errors
logging.getLogger("apscheduler").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["SMTP_USERNAME"] = "test@example.com"
os.environ["SMTP_PASSWORD"] = "test-password"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

from src.main import app
from src.database import get_db, Base
from src.models import User, Admin, TokenBlacklist
from src.services.auth_service import hash_password

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db():
    """Create test database tables and provide session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
    }


@pytest.fixture
def test_admin_data():
    """Test admin data"""
    return {
        "username": "admin",
        "password": "AdminPassword123!",
    }


@pytest.fixture
def create_test_user(db, test_user_data):
    """Create a test user in database"""
    user = User(
        email=test_user_data["email"],
        password=hash_password(test_user_data["password"]),
        is_email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def create_test_admin(db, test_admin_data):
    """Create a test admin in database"""
    admin = Admin(
        username=test_admin_data["username"],
        password=hash_password(test_admin_data["password"])
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(client, create_test_user, test_user_data):
    """Get authentication headers for test user"""
    response = client.post("/signin", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, create_test_admin, test_admin_data):
    """Get authentication headers for test admin"""
    response = client.post("/admin/signin", json={
        "username": test_admin_data["username"],
        "password": test_admin_data["password"]
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
