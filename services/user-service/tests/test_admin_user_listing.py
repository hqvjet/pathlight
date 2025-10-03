from datetime import datetime, timedelta
from collections.abc import Generator
import base64
import json
import hmac
import hashlib
import os
import sys
import types

import pytest
from fastapi import FastAPI
from fastapi.dependencies import utils as dependency_utils
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_PATH not in sys.path:
	sys.path.insert(0, SRC_PATH)

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key")

dependency_utils.ensure_multipart_is_installed = lambda: None  # type: ignore

if "jose" not in sys.modules:
	jose_module = types.ModuleType("jose")

	class _JWTError(Exception):
		pass

	class _JoseJWT:
		@staticmethod
		def encode(payload, key, algorithm="HS256"):
			if algorithm != "HS256":
				raise ValueError("Only HS256 supported in tests")
			header = {"alg": algorithm, "typ": "JWT"}
			segments = [
				_base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
				_base64url_encode(json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")),
			]
			signing_input = ".".join(segments).encode("utf-8")
			signature = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
			segments.append(_base64url_encode(signature))
			return ".".join(segments)

		@staticmethod
		def decode(token, key, algorithms=None):
			algorithms = algorithms or ["HS256"]
			if "HS256" not in algorithms:
				raise _JWTError("Unsupported algorithm")
			try:
				header_b64, payload_b64, signature_b64 = token.split(".")
			except ValueError as exc:
				raise _JWTError("Invalid token format") from exc

			signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
			expected_sig = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
			provided_sig = _base64url_decode(signature_b64)
			if not hmac.compare_digest(expected_sig, provided_sig):
				raise _JWTError("Signature verification failed")

			payload_json = _base64url_decode(payload_b64).decode("utf-8")
			return json.loads(payload_json)

	setattr(jose_module, "JWTError", _JWTError)
	setattr(jose_module, "jwt", _JoseJWT)

	sys.modules["jose"] = jose_module


def _base64url_encode(data: bytes) -> str:
	return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
	padding = '=' * (-len(data) % 4)
	return base64.urlsafe_b64decode(data + padding)

if "boto3" not in sys.modules:
	boto3_stub = types.ModuleType("boto3")

	def _client_stub(*args, **kwargs):
		return None

	setattr(boto3_stub, "client", _client_stub)
	sys.modules["boto3"] = boto3_stub

if "botocore" not in sys.modules:
	botocore_module = types.ModuleType("botocore")
	exceptions_module = types.ModuleType("botocore.exceptions")

	class _ClientError(Exception):
		def __init__(self, response, operation_name):
			super().__init__(response)
			self.response = response
			self.operation_name = operation_name

	setattr(exceptions_module, "ClientError", _ClientError)
	setattr(botocore_module, "exceptions", exceptions_module)

	sys.modules["botocore"] = botocore_module
	sys.modules["botocore.exceptions"] = exceptions_module

from src.config import config
from src.database import SessionLocal, engine
from src.models import Admin, Base, User
from src.routes.user_routes import router as user_router
from src.services.user_service_auth import jose_jwt


@pytest.fixture(scope="module")
def test_app() -> FastAPI:
	app = FastAPI()
	app.include_router(user_router, prefix="/user")
	return app


@pytest.fixture(autouse=True)
def reset_tables() -> Generator[None, None, None]:
	Base.metadata.drop_all(bind=engine)
	Base.metadata.create_all(bind=engine)
	yield
	Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
	session = SessionLocal()
	try:
		yield session
	finally:
		session.close()


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
	return TestClient(test_app)


def _create_admin_token(admin_id: str, role: str = "admin") -> str:
	payload = {
		"sub": admin_id,
		"type": "access",
		"role": role,
		"exp": datetime.utcnow() + timedelta(minutes=30),
	}
	return jose_jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def test_admin_can_list_users(client: TestClient, db_session: Session) -> None:
	admin = Admin(username="root", password="secret")
	user = User(
		email="learner@example.com",
		password="pwd",
		given_name="Learner",
		level=5,
	)
	db_session.add_all([admin, user])
	db_session.commit()

	token = _create_admin_token(str(admin.id))

	response = client.get(
		"/user/admin/users",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	data = response.json()
	assert data["status"] == 200
	assert isinstance(data["users"], list)
	assert len(data["users"]) == 1

	summary = data["users"][0]
	assert summary["user_id"] == user.id
	assert summary["email"] == user.email
	assert summary["given_name"] == user.given_name
	assert summary["level"] == user.level


def test_non_admin_cannot_list_users(client: TestClient, db_session: Session) -> None:
	admin = Admin(username="root", password="secret")
	user = User(email="learner@example.com", password="pwd")
	db_session.add_all([admin, user])
	db_session.commit()

	token = _create_admin_token(str(admin.id), role="user")

	response = client.get(
		"/user/admin/users",
		headers={"Authorization": f"Bearer {token}"},
	)

	assert response.status_code == 200
	data = response.json()
	assert data["status"] == 503
	assert data["message"] == "Bạn không có quyền truy cập"
	assert data["users"] == []
