import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["COURSE_SERVICE_SKIP_DB"] = "true"

from src.main import app
from src.database import Base
from src.models import Course, Lesson, LearningProgress
import src.database as _db

engine = create_engine(
    os.environ["DATABASE_URL"],
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
_db.engine = engine
_db.SessionLocal = SessionLocal


@pytest.fixture(scope="module", autouse=True)
def _configure_test_db():
    prev_engine = _db.engine
    prev_session = _db.SessionLocal
    _db.engine = engine
    _db.SessionLocal = SessionLocal
    yield
    _db.engine = prev_engine
    _db.SessionLocal = prev_session

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def seed_full_course():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        c_id = str(uuid.uuid4())
        course = Course(
            course_id=c_id,
            user_id="user-1",
            title="Course",
            overview="Desc",
            level="overview",
            duration=10,
            publish=False,
        )
        session.add(course)
        # lessons + progress
        lesson_ids = []
        for i in range(2):
            lid = str(uuid.uuid4())
            lesson = Lesson(
                lesson_id=lid,
                course_id=course.course_id,
                title=f"L{i}",
                overview="Desc",
                content="Content",
                duration=5,
            )
            session.add(lesson)
            lesson_ids.append(lid)
        lp = LearningProgress(
            user_id="user-1",
            course_id=course.course_id,
            num_finished_lesson=len(lesson_ids),
            num_total_lesson=len(lesson_ids),
        )
        session.add(lp)
        session.commit()
        yield {"course_id": c_id, "lesson_ids": lesson_ids}
    finally:
        session.close()


def _auth(mocker, user="user-1"):
    mocker.patch("src.controllers.course_controller.jwt.decode", return_value={"sub": user})
    mocker.patch("src.controllers.course_controller.jwt.get_unverified_claims", return_value={"sub": user})


def test_finish_course_success(mocker, client, seed_full_course):
    _auth(mocker)
    resp = client.put("/course/finish", json={"course_id": seed_full_course["course_id"]}, headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 200


def test_finish_course_not_all_lessons_done(mocker, client, seed_full_course):
    # create another course with unfinished lesson
    _auth(mocker)
    session = SessionLocal()
    try:
        c = Course(
            course_id=str(uuid.uuid4()),
            user_id="user-1",
            title="New",
            overview="d",
            level="overview",
            duration=5,
            publish=False,
        )
        session.add(c)
        lesson = Lesson(
            lesson_id=str(uuid.uuid4()),
            course_id=c.course_id,
            title="L",
            overview="D",
            content="C",
            duration=5,
        )
        session.add(lesson)
        session.commit()
        target = c.course_id
    finally:
        session.close()

    resp = client.put("/course/finish", json={"course_id": target}, headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 401  # controller now returns HTTP 401 directly
    data = resp.json()
    assert data["status"] == 401


def test_finish_lesson_success(mocker, client, seed_full_course):
    _auth(mocker)
    # Create new unfinished lesson for existing course
    session = SessionLocal()
    try:
        course_id = seed_full_course["course_id"]
        lid = str(uuid.uuid4())
        lesson = Lesson(
            lesson_id=lid,
            course_id=course_id,
            title="NewLesson",
            overview="D",
            content="C",
            duration=5,
        )
        session.add(lesson)
        session.commit()
    finally:
        session.close()

    resp = client.put(f"/course/{course_id}/lessons/{lid}/finish", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    assert resp.json()["status"] == 200


def test_finish_lesson_not_owner(mocker, client, seed_full_course):
    _auth(mocker, user="other")
    course_id = seed_full_course["course_id"]
    lid = seed_full_course["lesson_ids"][0]
    resp = client.put(f"/course/{course_id}/lessons/{lid}/finish", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 401  # controller now returns HTTP 401 directly
    assert resp.json()["status"] == 401
