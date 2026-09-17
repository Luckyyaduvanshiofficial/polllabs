import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.poll import PollAppearance
from app.services.poll_utils import coerce_appearance
from app.api.v1.polls import map_poll_to_response

client = TestClient(app)


def test_appearance_defaults():
    app_model = PollAppearance()
    assert app_model.theme == "minimal"
    assert app_model.bg is None
    assert app_model.radius == "rounded"
    assert app_model.font == "system"
    assert app_model.effect == "none"
    assert app_model.layout == "list"


def test_appearance_full_valid():
    app_model = PollAppearance(
        theme="whatsapp",
        bg="#DCF8C6",
        accent="#00A884",
        ink="#111B21",
        radius="pill",
        font="system",
        effect="confetti",
        layout="grid",
    )
    assert app_model.bg == "#dcf8c6"
    assert app_model.accent == "#00a884"


def test_appearance_rejects_bad_hex():
    with pytest.raises(ValidationError):
        PollAppearance(bg="not-a-color")
    with pytest.raises(ValidationError):
        PollAppearance(accent="#gggggg")
    with pytest.raises(ValidationError):
        PollAppearance(ink="red")


def test_appearance_rejects_bad_enums():
    with pytest.raises(ValidationError):
        PollAppearance(theme="myspace")
    with pytest.raises(ValidationError):
        PollAppearance(radius="squircle")
    with pytest.raises(ValidationError):
        PollAppearance(effect="fireworks")


def test_coerce_appearance_missing_and_garbage():
    assert coerce_appearance(None) is None
    assert coerce_appearance({}) is None
    assert coerce_appearance("whatsapp") is None
    assert coerce_appearance({"theme": "myspace"}) is None


def test_coerce_appearance_valid():
    result = coerce_appearance({"theme": "telegram", "accent": "#229ED9"})
    assert isinstance(result, PollAppearance)
    assert result.theme == "telegram"


def _base_poll(**overrides):
    poll = {
        "id": "poll1",
        "title": "Best chat app?",
        "options": [
            {"id": "a1", "text": "Telegram", "vote_count": 3},
            {"id": "a2", "text": "WhatsApp", "vote_count": 1},
        ],
        "total_votes": 4,
        "created": "2026-09-17T00:00:00Z",
        "updated": "2026-09-17T00:00:00Z",
    }
    poll.update(overrides)
    return poll


def test_map_response_carries_appearance():
    resp = map_poll_to_response(
        _base_poll(appearance={"theme": "story", "effect": "confetti"}),
        is_owner=True,
    )
    assert resp.appearance is not None
    assert resp.appearance.theme == "story"
    assert resp.appearance.effect == "confetti"


def test_map_response_legacy_poll_without_appearance():
    resp = map_poll_to_response(_base_poll(), is_owner=True)
    assert resp.appearance is None


def test_create_rejects_invalid_appearance_hex():
    response = client.post(
        "/api/v1/polls",
        headers={"Authorization": "Bearer test-token-123"},
        json={
            "title": "Which theme do you prefer?",
            "options": ["WhatsApp style", "Telegram style"],
            "visibility": "public",
            "appearance": {"theme": "whatsapp", "accent": "not-a-color"},
        },
    )
    assert response.status_code == 422
