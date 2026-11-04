import re

from fastapi.testclient import TestClient
from sqlalchemy import text

import main
import seed_data
from conftest import BACKEND_DIR
from database import engine


def count(table):
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def test_seed_users_only_use_the_reserved_example_domain():
    users = seed_data.TEACHERS + seed_data.STUDENTS
    assert len(users) == 20
    assert all(email.endswith("@example.com") for _, _, email in users)
    assert len({email for _, _, email in users}) == 20


def test_seed_source_contains_no_hardcoded_password():
    source = (BACKEND_DIR / "seed_data.py").read_text()
    assert not re.search(r"get_password_hash\(\s*[\"']", source)
    assert not re.search(r"Password: \w+\)", source)


def test_seed_password_comes_from_env_or_is_random(monkeypatch):
    monkeypatch.setenv("SEED_USER_PASSWORD", "chosen-for-this-run")
    assert seed_data.get_seed_password() == "chosen-for-this-run"

    monkeypatch.setenv("SEED_USER_PASSWORD", "")
    first, second = seed_data.get_seed_password(), seed_data.get_seed_password()
    assert first != second
    assert len(first) >= 16


def test_seeding_queues_no_mail_and_later_signups_mail_only_the_new_user(test_mysql, monkeypatch):
    seed_data.seed_database()
    assert count("Users") == 20
    assert count("Enrollments") > 0
    assert count("RegisterEmailQueue") == 0
    assert count("EnrollmentsEmailQueue") == 0

    sent_to = []

    def fake_send(to_email, **_):
        sent_to.append(to_email)
        return True, ""

    monkeypatch.setattr(main.gmail_service, "send_email", fake_send)
    response = TestClient(main.app).post("/users/", json={
        "first_name": "New", "last_name": "User", "email": "new.user@example.com",
        "password": "not-a-real-password", "is_teacher": False,
    })

    assert response.status_code == 200
    assert sent_to == ["new.user@example.com"]


def test_seeded_accounts_log_in_with_the_chosen_password(test_mysql, monkeypatch):
    monkeypatch.setenv("SEED_USER_PASSWORD", "chosen-for-this-run")
    seed_data.seed_database()
    email = seed_data.STUDENTS[0][2]
    client = TestClient(main.app)
    assert client.post("/login/", json={"email": email, "password": "chosen-for-this-run"}).status_code == 200
    assert client.post("/login/", json={"email": email, "password": "wrong"}).status_code == 401
