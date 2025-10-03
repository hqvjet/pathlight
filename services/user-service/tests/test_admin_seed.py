import pytest

from src.database import engine, SessionLocal
from src.models import Base, Admin
from src.services.admin_service import ensure_default_admin_account, create_admin_account


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_ensure_default_admin_account_creates_and_is_idempotent():
    created = ensure_default_admin_account()
    assert created is True

    session = SessionLocal()
    try:
        admin = session.query(Admin).filter_by(username="admin").first()
        assert admin is not None
        assert admin.password == "admin"
    finally:
        session.close()

    created_again = ensure_default_admin_account()
    assert created_again is False


def test_create_admin_account_creates_new_admin():
    admin = create_admin_account("root", "secret")
    assert isinstance(admin.id, str)
    assert getattr(admin, "username") == "root"

    with SessionLocal() as session:
        stored = session.query(Admin).filter_by(username="root").one()
    assert getattr(stored, "password") == "secret"


def test_create_admin_account_overwrite_password():
    create_admin_account("alice", "oldpass")

    with pytest.raises(ValueError):
        create_admin_account("alice", "newpass")

    updated = create_admin_account("alice", "newpass", overwrite=True)
    assert getattr(updated, "username") == "alice"

    with SessionLocal() as session:
        stored = session.query(Admin).filter_by(username="alice").one()
    assert getattr(stored, "password") == "newpass"
