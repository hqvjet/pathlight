import os
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("POSTGRES_DSN", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test")

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from src.main import app
from src.core.database import Base, get_db
from src.core.security import hash_password
from src.models.user import User, UserProfile

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True, scope="module")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_login_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/auth/login", data={"username": "none", "password": "bad"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_login_success():
    async with TestSessionLocal() as db:
        from datetime import date
        profile = UserProfile(first_name="a", last_name="b", dob=date(2000, 1, 1), sex=True)
        user = User(email="u@example.com", password=hash_password("pass"), profile=profile)
        db.add(user)
        await db.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/auth/login", data={"username": "u@example.com", "password": "pass"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]
