"""Backend tests for the Mergington High School API.

Tests are structured with the AAA (Arrange-Act-Assert) pattern and use
FastAPI's TestClient to exercise the endpoints in memory.
"""

import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Snapshot and restore the in-memory database around each test."""
    # Arrange (shared): keep original state and restore it after the test
    snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "participants" in data["Chess Club"]


def test_signup_adds_new_participant(client):
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/Chess Club/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in activities["Chess Club"]["participants"]


def test_signup_duplicate_participant_returns_400(client):
    # Arrange
    email = "michael@mergington.edu"  # already registered in Chess Club

    # Act
    response = client.post(f"/activities/Chess Club/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_unknown_activity_returns_404(client):
    # Act
    response = client.post(
        "/activities/Unknown Club/signup?email=student@mergington.edu"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_existing_participant(client):
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/Chess Club/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_missing_participant_returns_404(client):
    # Act
    response = client.delete(
        "/activities/Chess Club/participants/notregistered@mergington.edu"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"


def test_unregister_unknown_activity_returns_404(client):
    # Act
    response = client.delete(
        "/activities/Unknown Club/participants/student@mergington.edu"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
