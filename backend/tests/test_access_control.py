"""Who may call what. The table below lists every route that needs a session, and
test_every_route_is_either_public_or_in_the_table fails if a new route is left out."""
from dataclasses import dataclass, field
from types import SimpleNamespace
from urllib.parse import quote

import pytest
from fastapi.routing import APIRoute

import auth
import main
import models
from database import Base, GCSDatabase

BUCKET_URL = "https://storage.googleapis.com/test-bucket"
PUBLIC_ROUTES = {("GET", "/"), ("POST", "/users/"), ("POST", "/login/")}
UPLOAD = {"files": {"file": ("a.txt", b"content", "text/plain")}}


class FakeBlob:
    def __init__(self, path):
        self.public_url = f"{BUCKET_URL}/{path}"

    def upload_from_string(self, *_, **__):
        pass

    def generate_signed_url(self, **_):
        return "https://storage.googleapis.com/signed-by-fake"

    def delete(self):
        pass


class FakeBucket:
    name = "test-bucket"

    def blob(self, path):
        return FakeBlob(path)


def add_user(session, name, **fields):
    user = models.User(first_name=name, last_name="Test", email=f"{name}@example.com", password_hash="x", **fields)
    session.add(user)
    session.flush()
    return user


@pytest.fixture
def world(db_session, monkeypatch):
    """A course with an enrolled student, and people with no relation to it."""
    monkeypatch.setattr(main, "gcs_db", GCSDatabase(FakeBucket()))
    session = db_session
    owner = add_user(session, "owner", is_teacher=True)
    other_teacher = add_user(session, "other_teacher", is_teacher=True)
    student = add_user(session, "student")
    outsider = add_user(session, "outsider")
    admin = add_user(session, "admin", is_admin=True)

    course = models.Course(title="Course", teacher_id=owner.id, is_visible=True, is_enrollable=True)
    draft = models.Course(title="Draft", teacher_id=owner.id, is_visible=False, is_enrollable=True)
    session.add_all([course, draft])
    session.flush()
    assignment = models.Assignment(course_id=course.id, title="Task")
    open_assignment = models.Assignment(course_id=course.id, title="Open task")
    textblock = models.TextBlock(course_id=course.id, title="Post")
    file = models.File(course_id=course.id, file_name="f.txt", gcs_url=f"{BUCKET_URL}/files/courses/1/f.txt")
    session.add_all([assignment, open_assignment, textblock, file])
    session.flush()
    session.add_all([
        models.Enrollment(user_id=student.id, course_id=course.id),
        models.AssignmentSubmission(user_id=student.id, assignment_id=assignment.id),
    ])
    session.commit()
    return SimpleNamespace(
        owner=owner, other_teacher=other_teacher, student=student, outsider=outsider, admin=admin,
        course=course, draft=draft, assignment=assignment, open_assignment=open_assignment,
        textblock=textblock, file=file,
    )


@dataclass
class Rule:
    method: str
    route: str
    allowed: str
    denied: tuple = ()
    url: str = ""
    json: object = None
    upload: bool = False
    extra: dict = field(default_factory=dict)


COURSE_BODY = {"title": "New"}
RULES = [
    Rule("POST", "/logout/", "student"),
    Rule("GET", "/session/", "student"),

    Rule("GET", "/users/", "admin", ("student", "owner")),
    Rule("GET", "/users/{email}", "student", ("outsider", "owner"), url="/users/student@example.com"),
    Rule("PUT", "/users/{email}", "student", ("outsider", "owner", "admin"), url="/users/student@example.com",
         json={"first_name": "Renamed"}),
    Rule("PUT", "/users/{email}/teacher", "admin", ("student", "owner"), url="/users/student@example.com/teacher",
         json={"is_teacher": True}),

    Rule("POST", "/courses/", "owner", ("student", "outsider", "admin"), json=COURSE_BODY),
    Rule("GET", "/courses/", "student"),
    Rule("GET", "/courses/teaching", "owner"),
    Rule("GET", "/courses/available", "student"),
    Rule("GET", "/courses/{course_id}", "student", url="/courses/{course}"),
    Rule("PUT", "/courses/{course_id}", "owner", ("student", "outsider", "other_teacher"), url="/courses/{course}",
         json=COURSE_BODY),
    Rule("DELETE", "/courses/{course_id}", "owner", ("student", "outsider", "other_teacher"), url="/courses/{course}"),
    Rule("PATCH", "/courses/{course_id}/image", "owner", ("student", "outsider", "other_teacher"),
         url="/courses/{course}/image", upload=True),

    Rule("GET", "/proxy-image", "student", url=f"/proxy-image?url={quote(BUCKET_URL + '/courses/1/a.png', safe='')}"),

    Rule("POST", "/assignments/", "owner", ("student", "outsider", "other_teacher"),
         json={"title": "T", "course_id": "{course}"}),
    Rule("GET", "/assignments/course/{course_id}", "student", ("outsider", "other_teacher"),
         url="/assignments/course/{course}"),
    Rule("PUT", "/assignments/{assignment_id}", "owner", ("student", "outsider", "other_teacher"),
         url="/assignments/{assignment}", json={"title": "T2"}),
    Rule("DELETE", "/assignments/{assignment_id}", "owner", ("student", "outsider", "other_teacher"),
         url="/assignments/{assignment}"),

    Rule("POST", "/submissions/", "student", ("outsider", "other_teacher", "owner"),
         json={"assignment_id": "{open_assignment}"}),
    Rule("GET", "/submissions/course/{course_id}/me", "student", ("outsider", "other_teacher"),
         url="/submissions/course/{course}/me"),
    Rule("DELETE", "/submissions/assignment/{assignment_id}/me", "student",
         url="/submissions/assignment/{assignment}/me"),

    Rule("POST", "/textblocks/", "owner", ("student", "outsider", "other_teacher"),
         json={"title": "P", "course_id": "{course}"}),
    Rule("GET", "/textblocks/course/{course_id}", "student", ("outsider", "other_teacher"),
         url="/textblocks/course/{course}"),
    Rule("DELETE", "/textblocks/{textblock_id}", "owner", ("student", "outsider", "other_teacher"),
         url="/textblocks/{textblock}"),

    Rule("POST", "/enrollments/", "outsider", ("owner",), json={"course_id": "{course}"}),
    Rule("DELETE", "/enrollments/", "student", json={"course_id": "{course}"}),
    Rule("GET", "/enrollments/me", "student"),
    Rule("GET", "/enrollments/course/{course_id}", "student", ("outsider", "other_teacher"),
         url="/enrollments/course/{course}"),

    Rule("POST", "/files/upload", "student", upload=True),
    Rule("GET", "/files/course/{course_id}", "student", ("outsider", "other_teacher"), url="/files/course/{course}"),
    Rule("POST", "/files/course/{course_id}", "owner", ("student", "outsider", "other_teacher"),
         url="/files/course/{course}", upload=True),
    Rule("GET", "/files/{file_id}", "student", ("outsider", "other_teacher"), url="/files/{file}"),
    Rule("DELETE", "/files/{file_id}", "owner", ("student", "outsider", "other_teacher"), url="/files/{file}"),
]
RULE_IDS = [f"{rule.method} {rule.route}" for rule in RULES]
UNSAFE_RULES = [rule for rule in RULES if rule.method != "GET"]
DENIED_CASES = [(rule, role) for rule in RULES for role in rule.denied]
DENIED_IDS = [f"{rule.method} {rule.route} as {role}" for rule, role in DENIED_CASES]


def fill(value, world):
    ids = dict(
        course=world.course.id, assignment=world.assignment.id, open_assignment=world.open_assignment.id,
        textblock=world.textblock.id, file=world.file.id,
    )
    if isinstance(value, str):
        return int(value.format(**ids)) if value.startswith("{") else value.format(**ids)
    if isinstance(value, dict):
        return {key: fill(item, world) for key, item in value.items()}
    return value


def call(client, rule, world):
    url = rule.url or rule.route
    if "{" in url:
        url = url.format(course=world.course.id, assignment=world.assignment.id, textblock=world.textblock.id,
                         file=world.file.id)
    kwargs = dict(rule.extra)
    if rule.json is not None:
        kwargs["json"] = fill(rule.json, world)
    if rule.upload:
        kwargs.update(UPLOAD)
    return client.request(rule.method, url, follow_redirects=False, **kwargs)


def snapshot(session):
    session.expire_all()
    return {table.name: sorted(map(repr, session.execute(table.select()).all())) for table in Base.metadata.sorted_tables}


# ---------- the table is complete ----------

def test_every_route_is_either_public_or_in_the_table():
    app_routes = {
        (method, route.path)
        for route in main.app.routes if isinstance(route, APIRoute)
        for method in route.methods
    }
    assert app_routes - PUBLIC_ROUTES == {(rule.method, rule.route) for rule in RULES}


def test_public_routes_stay_public(client, db_session):
    assert client.get("/").status_code == 200
    body = {"first_name": "A", "last_name": "B", "email": "a@example.com", "password": "not-a-real-password"}
    assert client.post("/users/", json=body).status_code == 200
    assert client.post("/login/", json={"email": "a@example.com", "password": "not-a-real-password"}).status_code == 200


# ---------- every route, by caller ----------

@pytest.mark.parametrize("rule", RULES, ids=RULE_IDS)
def test_anonymous_request_is_rejected_and_changes_nothing(client, db_session, world, rule):
    before = snapshot(db_session)

    response = call(client, rule, world)

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert snapshot(db_session) == before


@pytest.mark.parametrize("rule, role", DENIED_CASES, ids=DENIED_IDS)
def test_wrong_user_is_rejected_and_changes_nothing(as_user, db_session, world, rule, role):
    client = as_user(getattr(world, role))
    before = snapshot(db_session)

    response = call(client, rule, world)

    # Enrolling in your own course is a 400 with its own message, tested below.
    assert response.status_code == (400 if rule.route == "/enrollments/" else 403)
    assert snapshot(db_session) == before


@pytest.mark.parametrize("rule", RULES, ids=RULE_IDS)
def test_the_right_user_is_allowed(as_user, db_session, world, rule):
    response = call(as_user(getattr(world, rule.allowed)), rule, world)
    assert response.status_code < 400, response.text


@pytest.mark.parametrize("rule", UNSAFE_RULES, ids=[f"{r.method} {r.route}" for r in UNSAFE_RULES])
def test_state_changing_request_without_a_csrf_token_is_rejected(as_user, db_session, world, rule):
    client = as_user(getattr(world, rule.allowed))
    del client.headers[auth.CSRF_HEADER]
    before = snapshot(db_session)

    response = call(client, rule, world)

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid CSRF token"}
    assert snapshot(db_session) == before


# ---------- identity comes from the session ----------

@pytest.mark.parametrize("method, path, body", [
    ("POST", "/enrollments/", {"course_id": 0, "user_id": 0}),
    ("DELETE", "/enrollments/", {"course_id": 0, "user_id": 0}),
    ("POST", "/submissions/", {"assignment_id": 0, "user_id": 0}),
    ("POST", "/courses/", {"title": "T", "teacher_id": 0}),
    ("PUT", "/courses/1", {"title": "T", "teacher_id": 0}),
    ("POST", "/assignments/", {"title": "T", "course_id": 1, "user_id": 0}),
    ("PUT", "/assignments/1", {"title": "T", "user_id": 0}),
    ("POST", "/textblocks/", {"title": "T", "course_id": 1, "teacher_id": 0}),
    ("POST", "/login/", {"email": "owner@example.com", "password": "x", "is_admin": True}),
])
def test_identity_fields_in_the_request_are_refused(as_user, db_session, world, method, path, body):
    client = as_user(world.owner)
    before = snapshot(db_session)

    response = client.request(method, path, json=body)

    assert response.status_code == 422
    assert snapshot(db_session) == before


def test_new_course_belongs_to_the_caller(as_user, world):
    response = as_user(world.other_teacher).post("/courses/", json={"title": "Mine"})

    assert response.status_code == 200
    assert response.json()["teacher_id"] == world.other_teacher.id


def test_enrollment_belongs_to_the_caller(as_user, db_session, world):
    response = as_user(world.outsider).post("/enrollments/", json={"course_id": world.course.id})

    assert response.status_code == 200
    assert response.json()["user_id"] == world.outsider.id
    assert db_session.query(models.Enrollment).filter_by(user_id=world.outsider.id, course_id=world.course.id).count() == 1


def test_leaving_removes_only_the_callers_enrollment_and_submissions(as_user, db_session, world):
    db_session.add(models.Enrollment(user_id=world.outsider.id, course_id=world.course.id))
    db_session.add(models.AssignmentSubmission(user_id=world.outsider.id, assignment_id=world.assignment.id))
    db_session.commit()

    response = as_user(world.outsider).request("DELETE", "/enrollments/", json={"course_id": world.course.id})

    assert response.json() == {"message": "Successfully unenrolled", "status": "success"}
    assert db_session.query(models.Enrollment).filter_by(course_id=world.course.id).one().user_id == world.student.id
    assert db_session.query(models.AssignmentSubmission).one().user_id == world.student.id


def test_leaving_a_course_you_are_not_in_changes_nothing(as_user, db_session, world):
    client = as_user(world.outsider)
    before = snapshot(db_session)

    response = client.request("DELETE", "/enrollments/", json={"course_id": world.course.id})

    assert response.json() == {"message": "No enrollment found to delete", "status": "no_change"}
    assert snapshot(db_session) == before


def test_my_lists_show_only_the_caller(as_user, db_session, world):
    client = as_user(world.student)
    assert [e["user_id"] for e in client.get("/enrollments/me").json()] == [world.student.id]
    submissions = client.get(f"/submissions/course/{world.course.id}/me").json()
    assert [s["user_id"] for s in submissions] == [world.student.id]
    assert as_user(world.owner).get(f"/submissions/course/{world.course.id}/me").json() == []
    assert [c["id"] for c in as_user(world.other_teacher).get("/courses/teaching").json()] == []
    assert len(as_user(world.owner).get("/courses/teaching").json()) == 2


def test_deleting_a_submission_only_touches_the_callers_own(as_user, db_session, world):
    db_session.add(models.Enrollment(user_id=world.outsider.id, course_id=world.course.id))
    db_session.commit()

    response = as_user(world.outsider).delete(f"/submissions/assignment/{world.assignment.id}/me")

    assert response.status_code == 404
    assert db_session.query(models.AssignmentSubmission).one().user_id == world.student.id

    assert as_user(world.student).delete(f"/submissions/assignment/{world.assignment.id}/me").status_code == 200
    assert db_session.query(models.AssignmentSubmission).count() == 0


# ---------- submissions ----------

def test_a_student_cannot_grade_their_own_submission(as_user, db_session, world):
    client = as_user(world.student)
    before = snapshot(db_session)

    response = client.post(
        "/submissions/", json={"assignment_id": world.open_assignment.id, "grade": 10},
    )

    assert response.status_code == 422
    assert snapshot(db_session) == before


@pytest.mark.parametrize("url", [
    "javascript:alert(1)",
    "https://evil.example/a.pdf",
    "https://storage.googleapis.com/other-bucket/files/uploads/a.pdf",
    f"{BUCKET_URL}/courses/1/a.png",
    f"{BUCKET_URL}/files/uploads/../../courses/a.png",
])
def test_a_submission_must_point_at_an_upload_in_our_bucket(as_user, db_session, world, url):
    client = as_user(world.student)
    before = snapshot(db_session)

    response = client.post(
        "/submissions/", json={"assignment_id": world.open_assignment.id, "submission_file_url": url},
    )

    assert response.status_code == 400
    assert snapshot(db_session) == before


def test_a_submission_keeps_a_valid_upload_url(as_user, world):
    url = f"{BUCKET_URL}/files/uploads/a.pdf"

    response = as_user(world.student).post(
        "/submissions/", json={"assignment_id": world.open_assignment.id, "submission_file_url": url},
    )

    assert response.status_code == 200
    assert response.json()["submission_file_url"] == url
    assert response.json()["grade"] is None


# ---------- course visibility and enrollment ----------

def test_a_draft_course_is_hidden_from_people_outside_it(as_user, world):
    client = as_user(world.outsider)
    assert client.get(f"/courses/{world.draft.id}").status_code == 403
    assert world.draft.id not in [c["id"] for c in client.get("/courses/").json()]
    assert world.draft.id not in [c["id"] for c in client.get("/courses/available").json()]
    assert as_user(world.owner).get(f"/courses/{world.draft.id}").status_code == 200
    assert world.draft.id in [c["id"] for c in as_user(world.owner).get("/courses/").json()]


def test_an_enrolled_student_still_sees_a_course_that_became_a_draft(as_user, db_session, world):
    world.course.is_visible = False
    db_session.commit()
    assert as_user(world.student).get(f"/courses/{world.course.id}").status_code == 200


def test_you_cannot_enroll_in_a_draft(as_user, db_session, world):
    client = as_user(world.outsider)
    before = snapshot(db_session)
    response = client.post("/enrollments/", json={"course_id": world.draft.id})
    assert response.status_code == 403
    assert snapshot(db_session) == before


def test_you_cannot_enroll_in_a_closed_course(as_user, db_session, world):
    world.course.is_enrollable = False
    db_session.commit()
    client = as_user(world.outsider)
    before = snapshot(db_session)
    response = client.post("/enrollments/", json={"course_id": world.course.id})
    assert response.status_code == 403
    assert snapshot(db_session) == before


def test_duplicate_enrollment_and_enrolling_in_your_own_course_still_fail(as_user, world):
    assert as_user(world.student).post("/enrollments/", json={"course_id": world.course.id}).status_code == 400
    response = as_user(world.owner).post("/enrollments/", json={"course_id": world.course.id})
    assert response.status_code == 400
    assert response.json() == {"detail": "You cannot enroll in your own course"}


def test_available_courses_leave_out_your_own_and_your_enrollments(as_user, world):
    assert world.course.id in [c["id"] for c in as_user(world.outsider).get("/courses/available").json()]
    assert world.course.id not in [c["id"] for c in as_user(world.student).get("/courses/available").json()]
    assert world.course.id not in [c["id"] for c in as_user(world.owner).get("/courses/available").json()]


def test_leaving_a_course_ends_access_to_its_content(as_user, world):
    client = as_user(world.student)
    assert client.get(f"/textblocks/course/{world.course.id}").status_code == 200
    client.request("DELETE", "/enrollments/", json={"course_id": world.course.id})
    assert client.get(f"/textblocks/course/{world.course.id}").status_code == 403


# ---------- what other people's data shows ----------

def test_course_responses_do_not_show_the_teachers_email(as_user, world):
    response = as_user(world.outsider).get(f"/courses/{world.course.id}")
    assert response.json()["teacher"]["first_name"] == "owner"
    assert "owner@example.com" not in response.text


def test_only_the_teacher_sees_student_emails_in_the_roster(as_user, world):
    url = f"/enrollments/course/{world.course.id}"
    assert as_user(world.owner).get(url).json()[0]["user"]["email"] == "student@example.com"

    classmate_view = as_user(world.student).get(url).json()[0]["user"]
    assert classmate_view["first_name"] == "student"
    assert classmate_view["email"] is None


# ---------- teacher role and admin ----------

def test_signup_cannot_choose_to_be_a_teacher_or_admin(client, db_session):
    for field_name in ("is_teacher", "is_admin"):
        response = client.post("/users/", json={
            "first_name": "A", "last_name": "B", "email": "a@example.com",
            "password": "not-a-real-password", field_name: True,
        })
        assert response.status_code == 422
    assert db_session.query(models.User).count() == 0


def test_signup_creates_a_plain_student(client, db_session):
    response = client.post("/users/", json={
        "first_name": "A", "last_name": "B", "email": "a@example.com", "password": "not-a-real-password",
    })
    assert response.status_code == 200
    assert response.json()["is_teacher"] is False
    assert response.json()["is_admin"] is False


@pytest.mark.parametrize("field_name", ["is_teacher", "is_admin"])
def test_users_cannot_change_their_own_role(as_user, db_session, world, field_name):
    client = as_user(world.student)
    before = snapshot(db_session)
    response = client.put("/users/student@example.com", json={field_name: True})
    assert response.status_code == 422
    assert snapshot(db_session) == before


def test_users_can_still_edit_their_own_name(as_user, db_session, world):
    response = as_user(world.student).put("/users/student@example.com", json={"first_name": "Renamed"})
    assert response.status_code == 200
    db_session.expire_all()
    assert world.student.first_name == "Renamed"


def test_admin_can_grant_and_revoke_the_teacher_role(as_user, db_session, world):
    admin = as_user(world.admin)

    response = admin.put("/users/student@example.com/teacher", json={"is_teacher": True})

    assert response.status_code == 200
    assert response.json()["is_teacher"] is True
    assert as_user(world.student).post("/courses/", json=COURSE_BODY).status_code == 200

    assert admin.put("/users/student@example.com/teacher", json={"is_teacher": False}).status_code == 200
    db_session.expire_all()
    assert world.student.is_teacher is False
    assert as_user(world.student).post("/courses/", json=COURSE_BODY).status_code == 403


def test_the_teacher_route_cannot_grant_admin(as_user, db_session, world):
    response = as_user(world.admin).put("/users/student@example.com/teacher", json={"is_admin": True})
    assert response.status_code == 422
    db_session.expire_all()
    assert world.student.is_admin is False


def test_admin_gets_404_for_an_unknown_user(as_user, world):
    assert as_user(world.admin).put("/users/nobody@example.com/teacher", json={"is_teacher": True}).status_code == 404
    assert as_user(world.admin).get("/users/nobody@example.com").status_code == 404


def test_someone_elses_email_gets_403_whether_or_not_it_exists(as_user, world):
    assert as_user(world.student).get("/users/nobody@example.com").status_code == 403
    assert as_user(world.student).put("/users/nobody@example.com", json={"first_name": "X"}).status_code == 403


def test_admin_lists_users_without_password_hashes(as_user, world):
    response = as_user(world.admin).get("/users/")
    assert len(response.json()) == 5
    assert "password" not in response.text


def test_the_admin_role_gives_no_access_to_course_content(as_user, world):
    client = as_user(world.admin)
    assert client.get(f"/textblocks/course/{world.course.id}").status_code == 403
    assert client.delete(f"/courses/{world.course.id}").status_code == 403
