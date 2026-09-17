import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "polllabs-api"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "PollLabs API" in response.json()["message"]

def test_svg_badge_fallback():
    response = client.get("/api/v1/badges/non_existent_poll.svg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert "<svg" in response.text
    assert "not found" in response.text

def test_unauthorized_poll_creation():
    response = client.post(
        "/api/v1/polls/",
        json={
            "title": "Which language do you prefer?",
            "options": ["Python", "TypeScript", "Go"],
            "visibility": "public",
        },
    )
    # Without Auth header -> 401
    assert response.status_code == 401

def test_moderation_rejection_on_creation():
    response = client.post(
        "/api/v1/polls/",
        headers={"x-dev-user-id": "test-user-123"},
        json={
            "title": "Join this crypto-giveaway right now!",
            "options": ["Yes", "No"],
            "visibility": "public",
        },
    )
    assert response.status_code == 422
    assert "moderation failed" in response.json()["detail"]
