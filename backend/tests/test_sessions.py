import datetime

import pytest
from fastapi.testclient import TestClient

import auth
import main
import models

PASSWORD = "not-a-real-password"


@pytest.fixture
def user(db_session):
    user = models.User(
        first_name="Sam", last_name="Rivera", email="sam@example.com",
        password_hash=main.get_password_hash(PASSWORD),
    )
    db_session.add(user)
    db_session.commit()
    return user


def login(client, email="sam@example.com", password=PASSWORD):
    return client.post("/login/", json={"email": email, "password": password})


# ---------- passwords ----------

def test_passwords_are_stored_as_bcrypt_hashes_and_never_returned(client, db_session):
    response = client.post("/users/", json={
        "first_name": "New", "last_name": "User", "email": "new@example.com", "password": PASSWORD,
    })

    assert response.status_code == 200
    stored = db_session.query(models.User).filter_by(email="new@example.com").one().password_hash
    assert stored.startswith("$2b$")
    assert PASSWORD not in stored
    assert "password" not in response.text


# ---------- login ----------

def test_login_sets_an_http_only_cookie_and_returns_a_csrf_token(client, user):
    response = login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "sam@example.com"
    assert body["csrf_token"]
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{auth.SESSION_COOKIE_NAME}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Max-Age=" in cookie
    assert "password" not in response.text


def test_login_cookie_is_secure_when_configured(client, user, monkeypatch):
    monkeypatch.setattr(auth, "SESSION_COOKIE_SECURE", True)
    assert "Secure" in login(client).headers["set-cookie"]


def test_login_stores_only_a_hash_of_the_session_token(client, db_session, user):
    response = login(client)

    token = response.cookies[auth.SESSION_COOKIE_NAME]
    row = db_session.query(models.UserSession).one()
    assert row.user_id == user.id
    assert row.token_hash != token
    assert token not in row.token_hash


def test_login_with_a_wrong_password_sets_no_session(client, db_session, user):
    response = login(client, password="wrong")

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}
    assert "set-cookie" not in response.headers
    assert db_session.query(models.UserSession).count() == 0


def test_login_with_an_unknown_email_sets_no_session(client, db_session):
    response = login(client, email="nobody@example.com")

    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert db_session.query(models.UserSession).count() == 0


def test_login_again_replaces_the_previous_session(client, db_session, user):
    login(client)
    login(client)
    assert db_session.query(models.UserSession).count() == 1


def test_login_removes_expired_sessions(client, db_session, user):
    db_session.add(models.UserSession(
        token_hash="old", user_id=user.id, csrf_token="old",
        expires_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=1),
    ))
    db_session.commit()

    login(client)

    assert db_session.query(models.UserSession).filter_by(token_hash="old").count() == 0


# ---------- GET /session/ ----------

def test_session_returns_the_logged_in_user_and_the_same_csrf_token(client, user):
    csrf_token = login(client).json()["csrf_token"]

    response = client.get("/session/")

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "sam@example.com"
    assert response.json()["csrf_token"] == csrf_token


def test_session_rejects_an_anonymous_request(client, db_session):
    response = client.get("/session/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_session_rejects_a_made_up_cookie(client, db_session, user):
    client.cookies.set(auth.SESSION_COOKIE_NAME, "made-up")
    assert client.get("/session/").status_code == 401


def test_session_rejects_an_expired_session(client, db_session, user):
    login(client)
    row = db_session.query(models.UserSession).one()
    row.expires_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
    db_session.commit()

    assert client.get("/session/").status_code == 401


def test_session_lifetime_comes_from_configuration(client, db_session, user, monkeypatch):
    monkeypatch.setattr(auth, "SESSION_TTL_HOURS", 2)

    response = login(client)

    assert "Max-Age=7200" in response.headers["set-cookie"]
    row = db_session.query(models.UserSession).one()
    remaining = row.expires_at - datetime.datetime.utcnow()
    assert datetime.timedelta(hours=1, minutes=59) < remaining <= datetime.timedelta(hours=2)


# ---------- logout ----------

def test_logout_deletes_the_session_and_clears_the_cookie(client, db_session, user):
    csrf_token = login(client).json()["csrf_token"]

    response = client.post("/logout/", headers={auth.CSRF_HEADER: csrf_token})

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}
    assert db_session.query(models.UserSession).count() == 0
    assert f'{auth.SESSION_COOKIE_NAME}=""' in response.headers["set-cookie"]
    assert client.get("/session/").status_code == 401


def test_logged_out_token_cannot_be_reused(client, db_session, user):
    csrf_token = login(client).json()["csrf_token"]
    token = client.cookies[auth.SESSION_COOKIE_NAME]
    client.post("/logout/", headers={auth.CSRF_HEADER: csrf_token})

    other = TestClient(main.app, raise_server_exceptions=False)
    other.cookies.set(auth.SESSION_COOKIE_NAME, token)

    assert other.get("/session/").status_code == 401


def test_logout_rejects_an_anonymous_request(client, db_session):
    assert client.post("/logout/").status_code == 401


# ---------- CSRF ----------

def test_logout_without_a_csrf_token_is_rejected_and_keeps_the_session(client, db_session, user):
    login(client)

    response = client.post("/logout/")

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid CSRF token"}
    assert db_session.query(models.UserSession).count() == 1


def test_logout_with_a_wrong_csrf_token_is_rejected(client, db_session, user):
    login(client)

    assert client.post("/logout/", headers={auth.CSRF_HEADER: "wrong"}).status_code == 403
    assert db_session.query(models.UserSession).count() == 1


def test_a_csrf_token_from_another_session_is_rejected(client, db_session, user):
    other = TestClient(main.app, raise_server_exceptions=False)
    other_token = login(other).json()["csrf_token"]
    db_session.query(models.UserSession).delete()
    db_session.commit()
    login(client)

    assert client.post("/logout/", headers={auth.CSRF_HEADER: other_token}).status_code == 403


@pytest.mark.parametrize("path, body", [
    ("/login/", {"email": "sam@example.com", "password": PASSWORD}),
    ("/users/", {"first_name": "A", "last_name": "B", "email": "a@example.com", "password": PASSWORD}),
])
def test_login_and_signup_reject_an_untrusted_origin(client, db_session, user, path, body):
    response = client.post(path, json=body, headers={"Origin": "https://evil.example"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Origin not allowed"}
    assert "set-cookie" not in response.headers
    assert db_session.query(models.User).count() == 1


def test_login_accepts_an_allowed_origin(client, user):
    response = client.post(
        "/login/",
        json={"email": "sam@example.com", "password": PASSWORD},
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"


# ---------- CORS ----------

def preflight(client, origin):
    return client.options("/logout/", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": f"{auth.CSRF_HEADER},content-type",
    })


def test_cors_allows_a_configured_origin_with_the_csrf_header(client):
    response = preflight(client, "http://localhost:3000")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert auth.CSRF_HEADER.lower() in response.headers["access-control-allow-headers"].lower()


def test_cors_refuses_an_origin_that_is_not_configured(client):
    response = preflight(client, "https://evil.example")

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_gives_no_allow_origin_header_to_an_unknown_origin_on_a_simple_request(client):
    response = client.get("/", headers={"Origin": "https://evil.example"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


# ---------- configuration ----------

def test_origins_are_read_from_a_comma_separated_list():
    assert auth.parse_allowed_origins("https://a.example, https://b.example/") == [
        "https://a.example", "https://b.example",
    ]


def test_origins_default_to_the_local_frontend():
    assert auth.parse_allowed_origins(None) == ["http://localhost:3000"]


@pytest.mark.parametrize("value", ["*", "https://a.example,*"])
def test_a_wildcard_origin_stops_startup(value):
    with pytest.raises(RuntimeError, match="CORS_ALLOWED_ORIGINS"):
        auth.parse_allowed_origins(value)


@pytest.mark.parametrize("value, expected", [(None, True), ("", True), ("true", True), ("false", False), ("FALSE", False)])
def test_session_cookies_are_secure_unless_turned_off(value, expected):
    assert auth.parse_cookie_secure(value) is expected


@pytest.mark.parametrize("value, expected", [(None, "lax"), ("Strict", "strict"), ("none", "none")])
def test_same_site_is_read_from_configuration(value, expected):
    assert auth.parse_same_site(value) == expected


def test_an_unknown_same_site_value_stops_startup():
    with pytest.raises(RuntimeError, match="SESSION_COOKIE_SAMESITE"):
        auth.parse_same_site("sometimes")


def test_same_site_none_needs_a_secure_cookie():
    with pytest.raises(RuntimeError, match="SESSION_COOKIE_SAMESITE"):
        auth.parse_same_site("none", secure=False)
