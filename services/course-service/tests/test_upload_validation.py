from io import BytesIO

def test_requires_auth(client):
    resp = client.post("/course/upload/file", files={"files": ("a.pdf", b"x", "application/pdf")})
    assert resp.status_code == 403


def test_reject_bad_extension_with_auth(mocker, client):
    # fake a valid jwt decode returning sub
    mocker.patch("src.controllers.course_controller.jwt.decode", return_value={"sub": "u1"})
    resp = client.post(
        "/course/upload/file",
        headers={"Authorization": "Bearer token"},
        files={"files": ("a.txt", b"x", "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 401
    assert "không được hỗ trợ" in data["message"]


def test_reject_over_20mb_total(mocker, client):
    mocker.patch("src.controllers.course_controller.jwt.decode", return_value={"sub": "u1"})
    big = b"0" * (20 * 1024 * 1024 + 1)
    resp = client.post(
        "/course/upload/file",
        headers={"Authorization": "Bearer token"},
        files=[
            ("files", ("a.pdf", big, "application/pdf")),
        ],
    )
    data = resp.json()
    assert data["status"] == 401
    assert "vượt quá dung lượng" in data["message"]
