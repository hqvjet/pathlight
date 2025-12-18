def _auth(mocker):
    mocker.patch("src.controllers.course_controller.jwt.decode", return_value={"sub": "u1"})
    mocker.patch("src.controllers.course_controller.jwt.get_unverified_claims", return_value={"sub": "u1"})


def test_reject_empty_files(mocker, client):
    _auth(mocker)
    resp = client.post(
        "/course/upload/presign",
        headers={"Authorization": "Bearer token"},
        json={"items": []},
    )
    body = resp.json()
    assert body["status"] == 400


def test_reject_over_25mb_total(mocker, client):
    _auth(mocker)
    items = [{"filename": "file1.pdf", "content_type": "application/pdf", "size": 26 * 1024 * 1024}]
    resp = client.post(
        "/course/upload/presign",
        headers={"Authorization": "Bearer token"},
        json={"items": items},
    )
    body = resp.json()
    assert body["status"] == 400


def test_requires_auth(client):
    resp = client.post("/course/upload/file", files={"files": ("a.pdf", b"x", "application/pdf")})
    assert resp.status_code == 403


def test_reject_bad_extension_with_auth(mocker, client):
    _auth(mocker)
    resp = client.post(
        "/course/upload/file",
        headers={"Authorization": "Bearer token"},
        files={"files": ("a.txt", b"x", "text/plain")},
    )
    data = resp.json()
    assert data["status"] == 400
    assert "không được hỗ trợ" in data["message"]


def test_upload_file_over_20mb(mocker, client):
    _auth(mocker)
    big = b"0" * (25 * 1024 * 1024 + 1)
    resp = client.post(
        "/course/upload/file",
        headers={"Authorization": "Bearer token"},
        files=[
            ("files", ("a.pdf", big, "application/pdf")),
        ],
    )
    data = resp.json()
    assert data["status"] == 400
    assert "25MB" in data["message"]
