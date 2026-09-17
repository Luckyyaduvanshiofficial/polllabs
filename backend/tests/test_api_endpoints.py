import json
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
    # PRD §4.6: "no longer available"
    assert "no longer available" in response.text

def test_unauthorized_poll_creation():
    response = client.post(
        "/api/v1/polls",
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
        "/api/v1/polls",
        headers={"Authorization": "Bearer test-token-123"},
        json={
            "title": "Join this crypto-giveaway right now!",
            "options": ["Yes", "No"],
            "visibility": "public",
        },
    )
    assert response.status_code == 422
    assert "moderation failed" in response.json()["detail"]

def test_poll_report_abuse():
    response = client.post(
        "/api/v1/polls/fake_id_123/report",
        json={"reason": "Inappropriate or offensive question text"},
    )
    # When poll not found in db
    assert response.status_code == 404

def test_account_deletion_lifecycle():
    response = client.post(
        "/api/v1/auth/delete-account",
        headers={"Authorization": "Bearer test-user-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_deletion"
    assert "grace_period_ends_at" in data

    cancel_resp = client.post(
        "/api/v1/auth/cancel-delete-account",
        headers={"Authorization": "Bearer test-user-123"},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "active"
