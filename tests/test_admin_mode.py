import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import app as app_module
from fastapi.testclient import TestClient

client = TestClient(app_module.app)


def test_student_cannot_register_without_login():
    original = list(app_module.activities["Chess Club"]["participants"])
    try:
        response = client.post("/activities/Chess Club/signup?email=student@mergington.edu")
        assert response.status_code == 403
        assert response.json()["detail"] == "Teacher login required"
    finally:
        app_module.activities["Chess Club"]["participants"] = original


def test_teacher_can_register_student_after_login():
    original = list(app_module.activities["Chess Club"]["participants"])
    try:
        app_module.activities["Chess Club"]["participants"] = ["existing@mergington.edu"]

        login_response = client.post(
            "/admin/login",
            json={"username": "principal", "password": "mergington_admin"},
        )
        assert login_response.status_code == 200

        signup_response = client.post(
            "/activities/Chess Club/signup?email=student@mergington.edu"
        )
        assert signup_response.status_code == 200
        assert "student@mergington.edu" in app_module.activities["Chess Club"]["participants"]
    finally:
        app_module.activities["Chess Club"]["participants"] = original
