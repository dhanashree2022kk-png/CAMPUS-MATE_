"""Basic integration tests using an isolated temporary SQLite database."""
import os
import tempfile
from datetime import time
from pathlib import Path

# Set the database URI before importing the global Flask app so its SQLAlchemy
# engine is bound to an isolated file rather than the user's local demo DB.
_fd, _db_path = tempfile.mkstemp(prefix="campusmate_test_", suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = "sqlite:///" + Path(_db_path).as_posix()

import pytest
from app import app as flask_app, db, User, Notice, TimetableEntry


@pytest.fixture()
def app():
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SECRET_KEY="test-key")
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(full_name="Test Admin", email="admin@example.test", role="admin", is_active=True)
        admin.set_password("AdminPass123!")
        student = User(full_name="Test Student", email="student@example.test", student_id="STU-1", course="BCA", semester=3, section="A", role="student", is_active=True)
        student.set_password("StudentPass123!")
        teacher = User(full_name="Test Teacher", email="teacher@example.test", faculty_id="FAC-1", role="teacher", is_active=True)
        teacher.set_password("TeacherPass123!")
        db.session.add_all([admin, student, teacher])
        db.session.commit()
        db.session.add_all([
            Notice(title="Published notice", category="Examination", short_description="Short description", content="Full content", status="published", audience="students", created_by=admin.id),
            Notice(title="Draft notice", category="Assignment", short_description="Draft short", content="Draft content", status="draft", audience="students", created_by=admin.id),
            TimetableEntry(day_of_week="Monday", start_time=time(9), end_time=time(10), subject_name="Databases", faculty_name="Test Teacher", room_number="R1", course="BCA", semester=3, section="A"),
        ])
        db.session.commit()
    yield flask_app
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def test_home_and_database_initialization(app, client):
    assert client.get("/").status_code == 200
    with app.app_context():
        assert User.query.count() == 3
        assert Notice.query.count() == 2
        assert TimetableEntry.query.count() == 1


def test_login_logout_and_role_protection(client):
    response = login(client, "student@example.test", "StudentPass123!")
    assert response.status_code == 200
    assert b"Today's timetable" in response.data or b"Class timetable" in response.data
    assert client.get("/admin").status_code == 403
    assert client.post("/logout", follow_redirects=True).status_code == 200


def test_invalid_login(client):
    response = client.post("/login", data={"email": "student@example.test", "password": "wrong"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"incorrect" in response.data.lower()


def test_student_registration_and_duplicate_prevention(client, app):
    data = {"full_name": "New Student", "email": "new@example.test", "student_id": "NEW-1", "course": "BCA", "semester": "2", "section": "B", "password": "NewStudent123!", "confirm_password": "NewStudent123!"}
    response = client.post("/register", data=data, follow_redirects=True)
    assert b"account has been created" in response.data.lower()
    response2 = client.post("/register", data=data, follow_redirects=True)
    assert b"already exists" in response2.data.lower()
    with app.app_context():
        assert User.query.filter_by(email="new@example.test").count() == 1


def test_drafts_hidden_from_students(client):
    login(client, "student@example.test", "StudentPass123!")
    response = client.get("/notices")
    assert b"Published notice" in response.data
    assert b"Draft notice" not in response.data


def test_admin_can_create_notice(client, app):
    login(client, "admin@example.test", "AdminPass123!")
    response = client.post("/notices/create", data={"title": "New notice", "category": "General Announcement", "priority": "Normal", "short_description": "A new campus update", "content": "Please read this update.", "audience": "all", "status": "published", "event_date": "", "expires_at": ""}, follow_redirects=True)
    assert b"Notice saved successfully" in response.data
    with app.app_context():
        assert Notice.query.filter_by(title="New notice", status="published").count() == 1


def test_student_cannot_manage_timetable(client):
    login(client, "student@example.test", "StudentPass123!")
    assert client.get("/timetable/create").status_code == 403


def test_timetable_group_filter_and_teacher_dashboard(client):
    login(client, "student@example.test", "StudentPass123!")
    assert client.get("/timetable?view=week").status_code == 200
    client.post("/logout")
    response = login(client, "teacher@example.test", "TeacherPass123!")
    assert response.status_code == 200


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    try:
        os.unlink(_db_path)
    except OSError:
        pass
