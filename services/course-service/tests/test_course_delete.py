import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use unique database URL to avoid interference with other test files  
TEST_DB_URL = f"sqlite+pysqlite:///:memory:delete_test_{os.getpid()}"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("COURSE_SERVICE_SKIP_DB", "true")

from src.database import Base
from src.models import Course, CourseInfo, UnderstandLevelTag
from src.main import app

engine = create_engine(
    TEST_DB_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

import src.database as _db 
_db.engine = engine
_db.SessionLocal = SessionLocal


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="function")  # Changed from module to function for test isolation
def seed_db():
    Base.metadata.drop_all(bind=engine)  # Clean slate for each test
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        level = UnderstandLevelTag(understand_level_id=str(uuid.uuid4()), understand_level="average")
        session.add(level)
        session.flush()
        courses = []
        for i in range(2):
            ci_id = str(uuid.uuid4())
            c_id = str(uuid.uuid4())
            ci = CourseInfo(
                course_info_id=ci_id,
                understand_level_id=level.understand_level_id,
                title=f"Course {i}",
                description="Desc",
                duration=10,
                roadmap=None,
            )
            c = Course(
                course_id=c_id,
                course_info_id=ci.course_info_id,
                user_id="user-1",
                finish=False,
            )
            session.add(ci)
            session.add(c)
            courses.append(c_id)
        ci_other_id = str(uuid.uuid4())
        c_other_id = str(uuid.uuid4())
        ci_other = CourseInfo(
            course_info_id=ci_other_id,
            understand_level_id=level.understand_level_id,
            title="Other",
            description="Desc",
            duration=5,
            roadmap=None,
        )
        c_other = Course(
            course_id=c_other_id,
            course_info_id=ci_other.course_info_id,
            user_id="user-2",
            finish=False,
        )
        session.add(ci_other)
        session.add(c_other)
        session.commit()
        yield {"user_courses": courses, "other_course": c_other_id}
    finally:
        session.close()


def _auth(mocker, user_id="user-1"):
    mocker.patch("src.controllers.course_controller.jwt.decode", return_value={"sub": user_id})


def test_delete_single_success(mocker, client, seed_db):
    _auth(mocker, "user-1")
    target = seed_db["user_courses"][0]
    resp = client.delete(f"/course/delete", params={"course_id": target}, headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == 200

    session = SessionLocal()
    try:
        assert session.query(Course).filter_by(course_id=target).first() is None
    finally:
        session.close()


def test_delete_single_not_owner(mocker, client, seed_db):
    _auth(mocker, "user-1")
    other = seed_db["other_course"]
    resp = client.delete(f"/course/delete", params={"course_id": other}, headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 401
    data = resp.json()
    assert data["status"] == 401


def test_delete_all_success(mocker, client, seed_db):
    _auth(mocker, "user-1")
    resp = client.delete("/course/delete/all", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 200
    session = SessionLocal()
    try:
        assert session.query(Course).filter_by(user_id="user-1").count() == 0
        assert session.query(Course).filter_by(user_id="user-2").count() == 1
    finally:
        session.close()
