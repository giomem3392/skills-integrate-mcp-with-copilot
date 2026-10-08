"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import Cookie, FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

current_dir = Path(__file__).parent
TEACHERS_FILE = current_dir / "teachers.json"

# Mount the static files directory
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")


def load_teachers():
    if not TEACHERS_FILE.exists():
        default_teachers = {
            "teachers": {
                "principal": "mergington_admin",
                "coach": "activity_admin"
            }
        }
        TEACHERS_FILE.write_text(json.dumps(default_teachers, indent=2))
        return default_teachers["teachers"]

    with TEACHERS_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict) and "teachers" in data:
        return data["teachers"]
    return data if isinstance(data, dict) else {}


def require_teacher_session(teacher_session: Optional[str] = Cookie(default=None)):
    if not teacher_session:
        raise HTTPException(status_code=403, detail="Teacher login required")

    teachers = load_teachers()
    if teacher_session not in teachers:
        raise HTTPException(status_code=403, detail="Teacher session invalid")
    return teacher_session


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/admin/session")
def get_admin_session(teacher_session: Optional[str] = Cookie(default=None)):
    if not teacher_session or teacher_session not in load_teachers():
        return {"authenticated": False}
    return {"authenticated": True, "username": teacher_session}


@app.post("/admin/login")
def login_teacher(payload: dict):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    teachers = load_teachers()
    if teachers.get(username) != password:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    response = JSONResponse({"authenticated": True, "username": username})
    response.set_cookie(key="teacher_session", value=username, httponly=True, samesite="lax")
    return response


@app.post("/admin/logout")
def logout_teacher():
    response = JSONResponse({"authenticated": False, "message": "Logged out"})
    response.delete_cookie(key="teacher_session")
    return response


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    teacher_session: Optional[str] = Cookie(default=None)
):
    """Register a student for an activity. Only teachers may do this."""
    require_teacher_session(teacher_session)

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    teacher_session: Optional[str] = Cookie(default=None)
):
    """Remove a student from an activity. Only teachers may do this."""
    require_teacher_session(teacher_session)

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
