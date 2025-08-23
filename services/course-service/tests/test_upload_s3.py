import json
from io import BytesIO
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError


def _auth(mocker):
    mocker.patch("src.controllers.course_controller.jwt.decode", return_value={"sub": "u1"})


def test_upload_success(mocker, client):
    _auth(mocker)
    # Mock S3 client and its creation
    mock_s3 = mocker.Mock()
    mocker.patch("src.controllers.course_controller.boto3.client", return_value=mock_s3)

    # head_bucket ok
    # put_object ok

    resp = client.post(
        "/upload/file",
        headers={"Authorization": "Bearer tok"},
        files={"files": ("file.pdf", b"hello", "application/pdf")},
    )
    data = resp.json()
    assert data["status"] == 200
    assert len(data["uploaded_file"]) == 1
    # Ensure put_object called
    assert mock_s3.put_object.call_count == 1


def test_upload_endpoint_unreachable(mocker, client):
    _auth(mocker)
    mock_s3 = mocker.Mock()
    mock_s3.head_bucket.side_effect = EndpointConnectionError(endpoint_url="http://bad")
    mocker.patch("src.controllers.course_controller.boto3.client", return_value=mock_s3)

    resp = client.post(
        "/upload/file",
        headers={"Authorization": "Bearer tok"},
        files={"files": ("file.pdf", b"hello", "application/pdf")},
    )
    data = resp.json()
    assert data["status"] == 500
    assert "endpoint" in data["message"].lower()


def test_upload_missing_credentials(mocker, client):
    _auth(mocker)
    mock_s3 = mocker.Mock()
    mock_s3.head_bucket.side_effect = NoCredentialsError()
    mocker.patch("src.controllers.course_controller.boto3.client", return_value=mock_s3)

    resp = client.post(
        "/upload/file",
        headers={"Authorization": "Bearer tok"},
        files={"files": ("file.pdf", b"hello", "application/pdf")},
    )
    data = resp.json()
    assert data["status"] == 500
    assert "credentials" in data["message"].lower()


def test_upload_bucket_not_found(mocker, client):
    _auth(mocker)
    mock_s3 = mocker.Mock()
    error_response = {"Error": {"Code": "NoSuchBucket"}}
    mock_s3.head_bucket.side_effect = ClientError(error_response, "HeadBucket")
    mocker.patch("src.controllers.course_controller.boto3.client", return_value=mock_s3)

    resp = client.post(
        "/upload/file",
        headers={"Authorization": "Bearer tok"},
        files={"files": ("file.pdf", b"hello", "application/pdf")},
    )
    data = resp.json()
    assert data["status"] == 500
    assert "bucket" in data["message"].lower()
