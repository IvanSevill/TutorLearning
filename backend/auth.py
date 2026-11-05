"""Server-side sessions, CSRF protection and allowed origins."""
import datetime
import hashlib
import os
import secrets

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

import models
from database import get_db

SESSION_COOKIE_NAME = "tutorlearning_session"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000"]


def parse_allowed_origins(value):
    """Exact origins only: the browser sends the session cookie to whatever is allowed here"""
    origins = [origin.strip().rstrip("/") for origin in (value or "").split(",") if origin.strip()]
    if "*" in origins:
        raise RuntimeError("CORS_ALLOWED_ORIGINS cannot contain '*': list each frontend origin.")
    return origins or DEFAULT_ALLOWED_ORIGINS


def parse_cookie_secure(value):
    """Secure unless explicitly turned off, for local runs over plain http"""
    return (value or "true").strip().lower() != "false"


def parse_same_site(value, secure=True):
    same_site = (value or "lax").strip().lower()
    if same_site not in ("lax", "strict", "none"):
        raise RuntimeError("SESSION_COOKIE_SAMESITE must be lax, strict or none.")
    if same_site == "none" and not secure:
        raise RuntimeError("SESSION_COOKIE_SAMESITE=none needs SESSION_COOKIE_SECURE to stay on.")
    return same_site


ALLOWED_ORIGINS = parse_allowed_origins(os.getenv("CORS_ALLOWED_ORIGINS"))
SESSION_COOKIE_SECURE = parse_cookie_secure(os.getenv("SESSION_COOKIE_SECURE"))
SESSION_COOKIE_SAMESITE = parse_same_site(os.getenv("SESSION_COOKIE_SAMESITE"), SESSION_COOKIE_SECURE)
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS") or 12)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: models.User) -> tuple[str, str]:
    """Stores a new session and returns its (cookie token, CSRF token)"""
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    db.add(models.UserSession(
        token_hash=hash_token(token),
        user_id=user.id,
        csrf_token=csrf_token,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=SESSION_TTL_HOURS),
    ))
    db.commit()
    return token, csrf_token


def delete_session(db: Session, token: str) -> None:
    db.query(models.UserSession).filter(models.UserSession.token_hash == hash_token(token)).delete()
    db.commit()


def delete_expired_sessions(db: Session) -> None:
    db.query(models.UserSession).filter(models.UserSession.expires_at <= datetime.datetime.utcnow()).delete()
    db.commit()


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path="/",
    )


def get_current_session(request: Request, db: Session = Depends(get_db)) -> models.UserSession:
    """The caller's session. Every state-changing request must also carry its CSRF token"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    session = None
    if token:
        session = db.query(models.UserSession).filter(models.UserSession.token_hash == hash_token(token)).first()
    if not session or session.expires_at <= datetime.datetime.utcnow():
        raise HTTPException(status_code=401, detail="Not authenticated")

    if request.method not in SAFE_METHODS:
        sent_token = request.headers.get(CSRF_HEADER, "")
        if not secrets.compare_digest(sent_token.encode(), session.csrf_token.encode()):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
    return session


def get_current_user(session: models.UserSession = Depends(get_current_session)) -> models.User:
    return session.user


def require_trusted_origin(request: Request) -> None:
    """For routes that run before a session exists, where there is no CSRF token yet.
    A request with no Origin header does not come from another site's page."""
    origin = request.headers.get("origin")
    if origin is not None and origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Origin not allowed")
