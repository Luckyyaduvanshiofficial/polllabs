import json
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.polls import sanitize_poll_options_for_display
from tests.conftest import TEST_ADMIN_KEY

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "polls-lab-api"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Polls Lab API" in data["message"]
    assert data["docs"] == "/docs"

def test_svg_badge_fallback():
    response = client.get("/api/v1/badges/non_existent_poll.svg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert "<svg" in response.text
    assert "no longer available" in response.text

def test_png_badge_fallback():
    response = client.get("/api/v1/badges/non_existent_poll.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 50

def test_auth_urls():
    response = client.get("/api/v1/auth/github/url")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "github"
    assert "auth-with-oauth2" in data["auth_url"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer test-user-999"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["user_id"] == "test-user-999"

def test_unauthorized_poll_creation():
    response = client.post(
        "/api/v1/polls",
        json={
            "title": "Which language do you prefer?",
            "options": ["Python", "TypeScript", "Go"],
            "visibility": "public",
        },
    )
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

def test_result_display_masking_percentage():
    mock_poll = {
        "id": "poll1",
        "title": "Secret Poll",
        "owner": "owner_user",
        "total_votes": 100,
        "result_display": "show_percentage",
        "options": [
            {"id": "opt1", "text": "Option A", "vote_count": 60},
            {"id": "opt2", "text": "Option B", "vote_count": 40},
        ],
    }

    # Voter / Non-owner: raw counts and total_votes MUST BE masked (None)
    voter_options, voter_total = sanitize_poll_options_for_display(mock_poll, is_owner=False)
    assert voter_total is None
    assert voter_options[0].vote_count is None
    assert voter_options[0].percentage == 60.0
    assert voter_options[1].vote_count is None
    assert voter_options[1].percentage == 40.0

    # Owner: all raw counts and total_votes are visible
    owner_options, owner_total = sanitize_poll_options_for_display(mock_poll, is_owner=True)
    assert owner_total == 100
    assert owner_options[0].vote_count == 60
    assert owner_options[0].percentage == 60.0

def test_result_display_masking_hidden_until_close():
    mock_poll = {
        "id": "poll2",
        "title": "Future Result Poll",
        "owner": "owner_user",
        "total_votes": 50,
        "result_display": "hidden_until_close",
        "close_at": "2099-01-01T00:00:00Z",
        "options": [
            {"id": "opt1", "text": "Option A", "vote_count": 25},
            {"id": "opt2", "text": "Option B", "vote_count": 25},
        ],
    }

    # Voter: nothing shown until close
    voter_options, voter_total = sanitize_poll_options_for_display(mock_poll, is_owner=False)
    assert voter_total is None
    assert voter_options[0].vote_count is None
    assert voter_options[0].percentage is None

    # Owner: sees full counts
    owner_options, owner_total = sanitize_poll_options_for_display(mock_poll, is_owner=True)
    assert owner_total == 50
    assert owner_options[0].vote_count == 25
    assert owner_options[0].percentage == 50.0

def test_cors_origin_reflection_and_credentials():
    # Public health check with Origin
    res = client.get("/api/v1/health", headers={"Origin": "https://external-blog.org"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://external-blog.org"
    assert res.headers.get("access-control-allow-credentials") == "true"

    # Preflight OPTIONS on embed vote endpoint
    preflight = client.options(
        "/api/v1/votes/test-poll",
        headers={
            "Origin": "https://client-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, X-Device-Token",
        },
    )
    assert preflight.status_code == 204
    assert preflight.headers.get("access-control-allow-origin") == "https://client-site.com"
    assert "X-Device-Token" in preflight.headers.get("access-control-allow-headers", "")

def test_format_badge_data_formatting():
    from app.api.v1.badges import format_badge_data

    # Missing poll fallback
    label, val, err, url = format_badge_data(None)
    assert label == "poll"
    assert val == "no longer available"
    assert err is True

    # Open poll with breakdown
    sample_poll = {
        "id": "poll123",
        "title": "Favorite Framework?",
        "total_votes": 200,
        "result_display": "show_counts",
        "options": [
            {"id": "o1", "text": "Svelte", "vote_count": 140},
            {"id": "o2", "text": "React", "vote_count": 60},
        ],
    }
    badge_data = format_badge_data(sample_poll)
    assert badge_data.label == "Favorite Framework?"
    assert "Svelte 70% (200)" in badge_data.value
    assert badge_data.is_error is False
    assert "/polls/poll123" in badge_data.target_url

    # Tuple unpackability compatibility check
    label, val, err, url = badge_data
    assert label == badge_data.label
    assert url == badge_data.target_url

    # Hidden until close poll
    hidden_poll = {
        "id": "poll456",
        "title": "Election 2026",
        "total_votes": 500,
        "result_display": "hidden_until_close",
        "close_at": "2099-01-01T00:00:00Z",
        "options": [
            {"id": "o1", "text": "Candidate A", "vote_count": 300},
        ],
    }
    label, val, err, url = format_badge_data(hidden_poll)
    assert "results hidden until close" in val
    assert err is False

def test_purge_expired_accounts_admin_protection():
    from app.core.config import settings

    # Without admin key -> 403
    resp = client.post("/api/v1/auth/purge-expired-accounts")
    assert resp.status_code == 403

    # With invalid admin key -> 403
    resp_invalid = client.post(
        "/api/v1/auth/purge-expired-accounts",
        headers={"X-Admin-Key": "wrong-secret"},
    )
    assert resp_invalid.status_code == 403

    # With valid admin key -> 200
    valid_key = TEST_ADMIN_KEY
    resp_valid = client.post(
        "/api/v1/auth/purge-expired-accounts",
        headers={"X-Admin-Key": valid_key},
    )
    assert resp_valid.status_code == 200
    assert "purged_count" in resp_valid.json()

def test_trending_leaderboard_endpoint():
    resp = client.get("/api/v1/leaderboard/trending?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "leaderboard" in data
    assert "total" in data

