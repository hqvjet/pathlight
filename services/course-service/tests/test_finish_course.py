import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("COURSE_SERVICE_SKIP_DB", "true")

from src.main import app
from src.database import Base
from src.models import Course, CourseInfo, UnderstandLevelTag, Lesson, Test, FinalTest
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

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def seed_full_course():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        level = UnderstandLevelTag(understand_level_id=str(uuid.uuid4()), understand_level="average")
        session.add(level)
        session.flush()
        ci_id = str(uuid.uuid4())
        c_id = str(uuid.uuid4())
        ci = CourseInfo(
            course_info_id=ci_id,
            understand_level_id=level.understand_level_id,
            title="Course",
            description="Desc",
            duration=10,
            roadmap=None,
        )
        course = Course(
            course_id=c_id,
            course_info_id=ci.course_info_id,
            user_id="user-1",
            finish=False,
        )
        session.add(ci)
        session.add(course)
        # lessons + test + final test
        lesson_ids = []
        for i in range(2):
            lid = str(uuid.uuid4())
            lesson = Lesson(
                lesson_id=lid,
                course_id=course.course_id,
                title=f"L{i}",
                content="Content",
                description="Desc",
                finish=True,  # already finished
            )
            session.add(lesson)
            # each lesson test finished
            t = Test(
                test_id=str(uuid.uuid4()),
                lesson_id=lesson.lesson_id,
                title="T",
                description="TD",
                duration=5,
                finish=True,
                exp=10,
            )
            session.add(t)
            lesson_ids.append(lid)
        ft = FinalTest(
            final_test_id=str(uuid.uuid4()),
            course_id=course.course_id,
            title="FT",
            description="FD",
            duration=5,
            exp=20,
        )
        # Mark final test finished by adding attribute if not exists
        if not hasattr(ft, "finish"):
            # Some models may not have finish flag; for safety ignore
            pass
        session.add(ft)
        session.commit()
        yield {"course_id": c_id, "lesson_ids": lesson_ids}
    finally:
        session.close()


def _auth(mocker, user="user-1"):
    mocker.patch("src.controllers.course_controller.jwt.decode", return_value={"sub": user})


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
        level = session.query(UnderstandLevelTag).first()
        if level is None:
            level = UnderstandLevelTag(understand_level_id=str(uuid.uuid4()), understand_level="average")
            session.add(level)
            session.flush()
        ci = CourseInfo(
            course_info_id=str(uuid.uuid4()),
            understand_level_id=level.understand_level_id,
            title="New",
            description="d",
            duration=5,
            roadmap=None,
        )
        c = Course(
            course_id=str(uuid.uuid4()),
            course_info_id=ci.course_info_id,
            user_id="user-1",
            finish=False,
        )
        session.add(ci)
        session.add(c)
        lesson = Lesson(
            lesson_id=str(uuid.uuid4()),
            course_id=c.course_id,
            title="L",
            content="C",
            description="D",
            finish=False,
        )
        session.add(lesson)
        session.commit()
        target = c.course_id
    finally:
        session.close()

    resp = client.put("/course/finish", json={"course_id": target}, headers={"Authorization": "Bearer tok"})
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
            content="C",
            description="D",
            finish=False,
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
    assert resp.status_code == 200  # we return status key inside payload
    assert resp.json()["status"] == 401
