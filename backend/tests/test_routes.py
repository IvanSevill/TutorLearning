from urllib.parse import quote

import pytest

import main
import models
from database import GCSDatabase

BUCKET_URL = "https://storage.googleapis.com/test-bucket"
SIGNED_URL = "https://storage.googleapis.com/signed-by-fake"


class FakeBlob:
    def generate_signed_url(self, **_):
        return SIGNED_URL


class FakeBucket:
    name = "test-bucket"

    def blob(self, _):
        return FakeBlob()


@pytest.fixture
def configured_bucket(monkeypatch):
    monkeypatch.setattr(main, "gcs_db", GCSDatabase(FakeBucket()))


def get_proxy(client, url):
    return client.get(f"/proxy-image?url={quote(url, safe='')}", follow_redirects=False)


# ---------- /api/debug/seed ----------

def test_debug_seed_endpoint_is_gone(client):
    assert client.post("/api/debug/seed").status_code == 404
    assert "/api/debug/seed" not in {route.path for route in main.app.routes}


# ---------- /proxy-image ----------

REJECTED_URLS = [
    "https://evil.example/a.png",
    "//evil.example/a.png",
    "/\\evil.example/a.png",
    "https://storage.googleapis.com@evil.example/test-bucket/courses/a.png",
    "https://storage.googleapis.com:443@evil.example/test-bucket/courses/a.png",
    "https://storage.googleapis.com.evil.example/test-bucket/courses/a.png",
    "https://storage.googleapis.com\\@evil.example/test-bucket/courses/a.png",
    "http://storage.googleapis.com/test-bucket/courses/a.png",
    "https://storage.googleapis.com/other-bucket/courses/a.png",
    f"{BUCKET_URL}/files/uploads/submission.pdf",
    f"{BUCKET_URL}/courses/../files/uploads/submission.pdf",
    f"{BUCKET_URL}/courses/%2e%2e/files/uploads/submission.pdf",
    f"{BUCKET_URL}/courses/a.png\r\nX-Injected: 1",
    "files/uploads/submission.pdf",
    "courses/a.png",
    "",
]


@pytest.mark.parametrize("url", REJECTED_URLS)
def test_proxy_image_rejects_anything_but_a_cover_in_our_bucket(client, configured_bucket, url):
    response = get_proxy(client, url)
    assert response.status_code == 400
    assert "location" not in response.headers


def test_proxy_image_does_not_redirect_when_no_bucket_is_configured(client):
    response = get_proxy(client, "https://evil.example/a.png")
    assert response.status_code == 400
    assert "location" not in response.headers


def test_proxy_image_still_redirects_a_valid_cover_to_its_signed_url(client, configured_bucket):
    response = get_proxy(client, f"{BUCKET_URL}/courses/7/cover_a.png")
    assert response.status_code == 307
    assert response.headers["location"] == SIGNED_URL


# ---------- DELETE /courses/{id} ----------

def add_course_with_related_rows(session, email):
    teacher = models.User(first_name="T", last_name="T", email=email, password_hash="x", is_teacher=True)
    session.add(teacher)
    session.flush()
    course = models.Course(title="Course", teacher_id=teacher.id)
    session.add(course)
    session.flush()
    assignment = models.Assignment(course_id=course.id, title="A")
    session.add(assignment)
    session.flush()
    session.add_all([
        models.Enrollment(user_id=teacher.id, course_id=course.id),
        models.AssignmentSubmission(user_id=teacher.id, assignment_id=assignment.id),
        models.TextBlock(course_id=course.id, title="P"),
        models.File(course_id=course.id, file_name="f", gcs_url="u"),
    ])
    session.commit()
    return course.id, assignment.id


RELATED_MODELS = [models.Assignment, models.Enrollment, models.TextBlock, models.File]


def test_delete_course_removes_it_and_all_related_rows(client, db_session):
    course_id, _ = add_course_with_related_rows(db_session, "a@example.com")

    response = client.delete(f"/courses/{course_id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Course and all related data deleted"}
    assert db_session.query(models.Course).count() == 0
    assert db_session.query(models.AssignmentSubmission).count() == 0
    for model in RELATED_MODELS:
        assert db_session.query(model).count() == 0


def test_delete_course_leaves_other_courses_untouched(client, db_session):
    course_id, _ = add_course_with_related_rows(db_session, "a@example.com")
    other_id, other_assignment_id = add_course_with_related_rows(db_session, "b@example.com")

    assert client.delete(f"/courses/{course_id}").status_code == 200

    assert [c.id for c in db_session.query(models.Course).all()] == [other_id]
    assert db_session.query(models.AssignmentSubmission).one().assignment_id == other_assignment_id
    for model in RELATED_MODELS:
        assert db_session.query(model).count() == 1


def test_delete_unknown_course_still_returns_404(client, db_session):
    assert client.delete("/courses/999").status_code == 404
