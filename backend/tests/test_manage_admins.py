import pytest

import manage_admins
import models


@pytest.fixture
def user(db_session, monkeypatch):
    monkeypatch.setattr(manage_admins, "SessionLocal", lambda: db_session)
    user = models.User(first_name="A", last_name="B", email="a@example.com", password_hash="x")
    db_session.add(user)
    db_session.commit()
    return user


def is_admin(db_session):
    return db_session.query(models.User).filter_by(email="a@example.com").one().is_admin


def test_grant_makes_a_user_an_admin(user, db_session, capsys):
    assert manage_admins.main(["grant", "a@example.com"]) == 0
    assert is_admin(db_session) is True
    assert capsys.readouterr().out == "a@example.com is now an admin\n"


def test_revoke_removes_the_role(user, db_session, capsys):
    manage_admins.main(["grant", "a@example.com"])
    capsys.readouterr()

    assert manage_admins.main(["revoke", "a@example.com"]) == 0

    assert is_admin(db_session) is False
    assert capsys.readouterr().out == "a@example.com is no longer an admin\n"


def test_unknown_email_fails_and_changes_nothing(user, db_session, capsys):
    assert manage_admins.main(["grant", "nobody@example.com"]) == 1
    assert is_admin(db_session) is False
    assert capsys.readouterr().err == "No user with email nobody@example.com\n"


@pytest.mark.parametrize("args", [[], ["grant"], ["promote", "a@example.com"], ["grant", "a@example.com", "x"]])
def test_wrong_arguments_print_usage_and_change_nothing(user, db_session, capsys, args):
    assert manage_admins.main(args) == 2
    assert is_admin(db_session) is False
    assert "usage:" in capsys.readouterr().err
