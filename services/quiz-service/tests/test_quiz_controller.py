import os
import sys
import types

TEST_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_ROOT, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Stub pathlight_common before importing app modules that depend on it.
pathlight_common = types.ModuleType("pathlight_common")
pathlight_common.get_database_url = lambda: "sqlite:///:memory:"
pathlight_common.get_debug_mode = lambda: False
sys.modules.setdefault("pathlight_common", pathlight_common)

from src.controllers import quiz_controller
from src.database import Base
from src.models import Quiz, QuizCard
from src.schemas.quiz_schemas import CreateQuizRequest, QuizSubmitRequest, QuizSubmitAnswer


class FakeRequest:
    def __init__(self):
        self.headers = {"Authorization": "Bearer token"}


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def patch_db(monkeypatch, session_factory):
    monkeypatch.setattr(quiz_controller, "_get_db", lambda: session_factory())


@pytest.fixture(autouse=True)
def patch_auth(monkeypatch):
    monkeypatch.setattr(quiz_controller, "_verify_token", lambda request: "user-123")


def test_create_quiz_enqueues_job(monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", "https://example.com/queue")
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")

    sent_kwargs = {}

    def fake_send_generate_with_vectorize(**kwargs):
        sent_kwargs.update(kwargs)
        return {"MessageId": "mid-1"}

    class FakeS3:
        def head_object(self, Bucket, Key):
            return {"ContentLength": 1024}

    def fake_client(name, region_name=None):
        assert name == "s3"
        return FakeS3()

    monkeypatch.setattr(quiz_controller, "send_generate_with_vectorize", fake_send_generate_with_vectorize)
    monkeypatch.setattr(quiz_controller.boto3, "client", fake_client)

    body = CreateQuizRequest(
        duration=15,
        difficulty="easy",
        s3_keys=["users/user-123/doc.pdf"],
        num_questions=10,
    )

    resp = quiz_controller.create_quiz_controller(FakeRequest(), body)

    assert resp["status"] == 202
    assert resp["quiz_id"]
    assert sent_kwargs.get("quiz_id") == resp["quiz_id"]
    assert sent_kwargs.get("s3_keys") == ["users/user-123/doc.pdf"]
    assert sent_kwargs.get("job_type") == "GENERATE_QUIZ_WITH_VECTORIZE"


def test_create_quiz_requires_documents(monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", "https://example.com/queue")
    body = CreateQuizRequest(
        duration=15,
        difficulty="easy",
        s3_keys=[],  # Empty s3_keys
    )
    with pytest.raises(HTTPException) as exc:
        quiz_controller.create_quiz_controller(FakeRequest(), body)
    assert exc.value.status_code == 400
    assert "document" in exc.value.detail.lower()


def test_submit_quiz_scores_and_updates_best(session_factory, monkeypatch):
    session = session_factory()
    quiz = Quiz(
        quiz_id="quiz-1",
        user_id="user-123",
        publish=False,
        finish=False,
        title="Quiz Title",
        overview="Overview",
        level="easy",
        duration=10,
        num_questions=2,
    )
    card1 = QuizCard(
        card_id="card-1",
        quiz_id="quiz-1",
        question="Q1",
        hint=None,
        explanation="Because",
        difficulty="easy",
        option1="A",
        option2="B",
        option3="C",
        option4="D",
        answer=1,
    )
    card2 = QuizCard(
        card_id="card-2",
        quiz_id="quiz-1",
        question="Q2",
        hint=None,
        explanation="Because",
        difficulty="medium",
        option1="A",
        option2="B",
        option3="C",
        option4="D",
        answer=2,
    )
    session.add_all([quiz, card1, card2])
    session.commit()
    session.close()

    monkeypatch.setattr(quiz_controller, "_get_db", lambda: session_factory())

    body = QuizSubmitRequest(
        answers=[
            QuizSubmitAnswer(card_id="card-1", answer=1),
            QuizSubmitAnswer(card_id="card-2", answer=2),
        ]
    )

    resp = quiz_controller.submit_quiz_controller(FakeRequest(), "quiz-1", body)

    assert resp.status == 200
    assert resp.result.score == 100.0
    assert resp.result.correct_count == 2
    assert resp.result.total == 2

    with session_factory() as verify_session:
        refreshed = verify_session.query(Quiz).filter_by(quiz_id="quiz-1").first()
        assert refreshed.previous_score == 100