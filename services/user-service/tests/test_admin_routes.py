import os
import sys
import types
import json
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure src package modules can be imported like service runtime
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Provide baseline environment defaults for module imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_jwt_testing_12345")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

# Provide lightweight fallback for python-jose when unavailable in test env
if "jose" not in sys.modules:  # pragma: no cover
    jose_stub = types.ModuleType("jose")

    class JWTError(Exception):
        pass

    def _b64encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    def _b64decode(data: str) -> bytes:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)

    def _encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
        header = {"typ": "JWT", "alg": algorithm}
        segments = [
            _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode()),
            _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()),
        ]
        signing_input = ".".join(segments).encode()
        signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        segments.append(_b64encode(signature))
        return ".".join(segments)

    def _decode(token: str, secret: str, algorithms=None):
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
        except ValueError as exc:  # pragma: no cover
            raise JWTError("Token structure invalid") from exc
        signing_input = f"{header_b64}.{payload_b64}".encode()
        signature = _b64decode(signature_b64)
        expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise JWTError("Signature mismatch")
        payload = json.loads(_b64decode(payload_b64).decode())
        return payload

    setattr(jose_stub, "JWTError", JWTError)
    setattr(jose_stub, "jwt", types.SimpleNamespace(encode=_encode, decode=_decode))
    sys.modules["jose"] = jose_stub

from src.services.user_service_auth import jose_jwt

if "PIL" not in sys.modules:  # pragma: no cover
    pil_module = types.ModuleType("PIL")
    pil_image_module = types.ModuleType("Image")

    def _dummy_open(*args, **kwargs):  # minimal placeholder
        raise NotImplementedError("Image operations are not supported in tests")

    setattr(pil_image_module, "open", _dummy_open)
    setattr(pil_module, "Image", pil_image_module)
    sys.modules["PIL"] = pil_module
    sys.modules["PIL.Image"] = pil_image_module

if "requests" not in sys.modules:  # pragma: no cover
    requests_stub = types.ModuleType("requests")

    class _DummyResponse:
        status_code = 503

        def json(self):
            return {}

    def _dummy_request(*args, **kwargs):
        return _DummyResponse()

    setattr(requests_stub, "get", _dummy_request)
    setattr(requests_stub, "post", _dummy_request)
    sys.modules["requests"] = requests_stub

from src.main import app
from src.database import create_tables, SessionLocal
from src.models import User, Admin


def _issue_token(admin_id: str, role: str = "admin") -> str:
    secret = os.environ.get("JWT_SECRET_KEY", "")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    payload = {
        "sub": admin_id,
        "role": role,
        "type": "access",
        "exp": int(expires_at.timestamp()),
    }
    return jose_jwt.encode(payload, secret, algorithm=algorithm)


def _bootstrap_entities():
    create_tables()
    with SessionLocal() as session:
        session.query(Admin).delete()
        session.query(User).delete()
        admin = Admin(username="admin_test", password="secret")
        user = User(email="user@example.com", password="hashed")
        session.add(admin)
        session.add(user)
        session.commit()
        session.refresh(admin)
        session.refresh(user)
        return admin, user


def test_admin_users_listing_success(mock_env_vars):
    admin, user = _bootstrap_entities()
    client = TestClient(app)
    token = _issue_token(str(admin.id), role="admin")
    response = client.get(
        "/user/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert any(entry["user_id"] == user.id for entry in data["users"])
    matching = next(entry for entry in data["users"] if entry["user_id"] == user.id)
    assert matching["email"] == user.email
    assert matching["given_name"] == user.given_name


def test_admin_users_listing_forbidden(mock_env_vars):
    admin, _ = _bootstrap_entities()
    client = TestClient(app)
    token = _issue_token(str(admin.id), role="user")
    response = client.get(
        "/user/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert response.json() == {"status": 503, "message": "Bạn không có quyền truy cập"}
