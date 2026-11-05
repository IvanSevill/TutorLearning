"""Shared test setup.

The DB_* variables are always overwritten here, before any app module is
imported, so that no test can reach a database configured for real use.
Tests that need real MySQL triggers run only when TEST_DB_NAME is set.
"""
import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "")
TEST_DB_HOST = os.environ.get("TEST_DB_HOST", "127.0.0.1")

if TEST_DB_NAME and "test" not in TEST_DB_NAME:
    pytest.exit("TEST_DB_NAME must contain 'test': these tests drop every table.", returncode=2)
if TEST_DB_HOST not in ("127.0.0.1", "localhost"):
    pytest.exit("TEST_DB_HOST must be local: these tests drop every table.", returncode=2)

os.environ.update(
    DB_HOST=TEST_DB_HOST,
    DB_PORT=os.environ.get("TEST_DB_PORT", "1"),
    DB_USER=os.environ.get("TEST_DB_USER", "test"),
    DB_PASSWORD=os.environ.get("TEST_DB_PASSWORD", ""),
    DB_NAME=TEST_DB_NAME or "unused_test_db",
    # Empty values also stop a local .env from filling these in.
    INSTANCE_UNIX_SOCKET="",
    GCS_BUCKET_NAME="",
    GCP_PROJECT_ID="",
    GCP_PRIVATE_KEY="",
    GCP_CLIENT_EMAIL="",
    GMAIL_SENDER_EMAIL="",
    GMAIL_APP_PASSWORD="",
    SEED_USER_PASSWORD="",
    # The test client talks plain http, where a Secure cookie would not be sent back.
    SESSION_COOKIE_SECURE="false",
    SESSION_COOKIE_SAMESITE="",
    SESSION_TTL_HOURS="",
    CORS_ALLOWED_ORIGINS="",
    NO_GCE_CHECK="true",
)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import main  # noqa: E402
from database import Base, get_db  # noqa: E402


@pytest.fixture
def db_session():
    """In-memory SQLite with foreign keys enforced, as MySQL enforces them."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    main.app.dependency_overrides[get_db] = lambda: session
    yield session
    main.app.dependency_overrides.pop(get_db, None)
    session.close()
    engine.dispose()


@pytest.fixture
def client():
    """Does not run the startup event, which needs MySQL."""
    return TestClient(main.app, raise_server_exceptions=False)


@pytest.fixture
def test_mysql():
    if not TEST_DB_NAME:
        pytest.skip("Set TEST_DB_NAME, TEST_DB_PORT, TEST_DB_USER and TEST_DB_PASSWORD to run.")
