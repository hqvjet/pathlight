import asyncio
import types
import uuid
import json

import pytest


def _auth(mocker):
    mocker.patch("src.controllers.course_controller.jwt.decode", return_value={"sub": "user-123"})


class _AsyncResp:
    def __init__(self, status_code=200, text="ok"):
        self.status_code = status_code
        self.text = text


@pytest.mark.anyio
def test_create_course_success(mocker, client):
    _auth(mocker)

    # Mock httpx.AsyncClient so that first call (vectorize) and second call (generate) both return 200
    async def _post_ok(url, json=None, headers=None):  # noqa: A002
        return _AsyncResp(200, "ok")

    class _AsyncClientCtx:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return types.SimpleNamespace(post=_post_ok)
        async def __aexit__(self, exc_type, exc, tb):
            return False

    mocker.patch("src.controllers.course_controller.httpx.AsyncClient", _AsyncClientCtx)

    payload = {
        "title": "Lập trình",
        "description": "Desc",
        "understand_level": "average",
        "duration": 10,
        "uploaded_file": ["a.pdf"],
    }
    resp = client.post("/create", json=payload, headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 200
    assert "thành công" in data["message"].lower()


@pytest.mark.anyio
def test_create_course_missing_files(mocker, client):
    _auth(mocker)
    payload = {
        "title": "Lập trình",
        "description": "Desc",
        "understand_level": "average",
        "duration": 10,
        "uploaded_file": [],
    }
    resp = client.post("/create", json=payload, headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 401
    data = resp.json()
    assert data["status"] == 401
    assert "không tìm thấy file" in data["message"].lower()


@pytest.mark.anyio
def test_create_course_vectorize_fail(mocker, client):
    _auth(mocker)

    # First call fail (vectorize), ensure second isn't needed
    async def _post_fail(url, json=None, headers=None):  # noqa: A002
        return _AsyncResp(500, "fail")

    class _AsyncClientCtx:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return types.SimpleNamespace(post=_post_fail)
        async def __aexit__(self, exc_type, exc, tb):
            return False

    mocker.patch("src.controllers.course_controller.httpx.AsyncClient", _AsyncClientCtx)

    payload = {
        "title": "Lập trình",
        "description": "Desc",
        "understand_level": "average",
        "duration": 10,
        "uploaded_file": ["a.pdf"],
    }
    resp = client.post("/create", json=payload, headers={"Authorization": "Bearer tok"})
    # Vectorize fail returns 401 generic error per current controller logic
    assert resp.status_code == 401
    data = resp.json()
    assert data["status"] == 401
    assert "có lỗi" in data["message"].lower()