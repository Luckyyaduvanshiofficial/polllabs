import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.polls import sanitize_poll_options_for_display

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-token-123"}


# ---------------------------------------------------------------------------
# Unit tests: sanitize_poll_options_for_display
# ---------------------------------------------------------------------------

MOCK_POLL = {
    "id": "poll_001",
    "title": "Quiz Poll",
    "owner": "owner_user",
    "total_votes": 30,
    "result_display": "show_counts",
    "options": [
        {"id": "o1", "text": "Paris", "vote_count": 15},
        {"id": "o2", "text": "London", "vote_count": 10},
        {"id": "o3", "text": "Berlin", "vote_count": 5},
    ],
}


def test_quiz_mode_marks_correct_options():
    """When is_quiz=True and correct_options is set, is_correct is True/False per option."""
    opts, _ = sanitize_poll_options_for_display(
        MOCK_POLL,
        is_owner=False,
        is_quiz=True,
        correct_options=["o1", "o3"],
        show_voters=False,
        device_token="some-token",
        has_voted=True,
    )
    assert opts[0].is_correct is True
    assert opts[1].is_correct is False
    assert opts[2].is_correct is True


def test_quiz_mode_no_token_no_correct():
    """Before the viewer has voted, is_correct stays None even for quiz polls."""
    opts, _ = sanitize_poll_options_for_display(
        MOCK_POLL,
        is_owner=False,
        is_quiz=True,
        correct_options=["o1"],
        show_voters=False,
        device_token=None,
    )
    assert opts[0].is_correct is None


def test_non_quiz_poll_has_none_is_correct():
    """Non-quiz polls always return is_correct=None."""
    opts, _ = sanitize_poll_options_for_display(
        MOCK_POLL,
        is_owner=False,
        is_quiz=False,
        correct_options=None,
    )
    assert opts[0].is_correct is None


def test_show_voters_returns_empty_list():
    """When show_voters=True, voters field is initialized as empty list (populated by caller)."""
    opts, _ = sanitize_poll_options_for_display(
        MOCK_POLL,
        is_owner=False,
        is_quiz=False,
        show_voters=True,
        device_token="some-token",
    )
    assert opts[0].voters is not None
    assert isinstance(opts[0].voters, list)


def test_show_voters_hidden_until_close():
    """When hidden_until_close and not closed, voters should be None."""
    hidden_poll = {
        **MOCK_POLL,
        "result_display": "hidden_until_close",
        "close_at": "2099-01-01T00:00:00Z",
    }
    opts, _ = sanitize_poll_options_for_display(
        hidden_poll,
        is_owner=False,
        show_voters=True,
        device_token="some-token",
    )
    assert opts[0].voters is None


# ---------------------------------------------------------------------------
# Schema tests: VoteRequest accepts single and list option_id
# ---------------------------------------------------------------------------

def test_vote_request_single_option():
    from app.schemas.vote import VoteRequest
    v = VoteRequest(option_id="abc123")
    assert v.option_id == "abc123"


def test_vote_request_multi_option():
    from app.schemas.vote import VoteRequest
    v = VoteRequest(option_id=["abc123", "def456", "ghi789"])
    assert v.option_id == ["abc123", "def456", "ghi789"]
    assert len(v.option_id) == 3


def test_vote_request_empty_list_rejected():
    from app.schemas.vote import VoteRequest
    import pydantic
    try:
        VoteRequest(option_id=[])
        assert False, "Should have raised"
    except pydantic.ValidationError:
        pass


def test_vote_request_duplicate_ids_rejected():
    from app.schemas.vote import VoteRequest
    import pydantic
    try:
        VoteRequest(option_id=["abc", "abc"])
        assert False, "Should have raised"
    except pydantic.ValidationError:
        pass


# ---------------------------------------------------------------------------
# Schema tests: PollCreate accepts behavior fields
# ---------------------------------------------------------------------------

def test_poll_create_accepts_behavior_fields():
    from app.schemas.poll import PollCreate
    p = PollCreate(
        title="Test Quiz Poll",
        options=["A", "B", "C"],
        max_selections=3,
        is_quiz=True,
        correct_options=["o1", "o2"],
        show_voters=True,
    )
    assert p.max_selections == 3
    assert p.is_quiz is True
    assert p.correct_options == ["o1", "o2"]
    assert p.show_voters is True


def test_poll_create_defaults():
    from app.schemas.poll import PollCreate
    p = PollCreate(title="Basic Poll", options=["Yes", "No"])
    assert p.max_selections == 1
    assert p.is_quiz is False
    assert p.correct_options is None
    assert p.show_voters is False


def test_poll_response_includes_behavior_fields():
    from app.schemas.poll import PollResponse, PollOptionResponse
    r = PollResponse(
        id="x",
        title="t",
        options=[PollOptionResponse(id="o1", text="A")],
        visibility="public",
        result_display="show_counts",
        owner="owner",
        created="2026-01-01",
        updated="2026-01-01",
        max_selections=2,
        is_quiz=True,
        show_voters=True,
    )
    assert r.max_selections == 2
    assert r.is_quiz is True
    assert r.show_voters is True


# ---------------------------------------------------------------------------
# Schema tests: PollOptionResponse supports is_correct and voters
# ---------------------------------------------------------------------------

def test_poll_option_response_with_quiz_fields():
    from app.schemas.poll import PollOptionResponse
    o = PollOptionResponse(id="o1", text="Paris", is_correct=True, voters=["abc123..."])
    assert o.is_correct is True
    assert o.voters == ["abc123..."]


def test_poll_option_response_defaults():
    from app.schemas.poll import PollOptionResponse
    o = PollOptionResponse(id="o1", text="Paris")
    assert o.is_correct is None
    assert o.voters is None


# ---------------------------------------------------------------------------
# API tests: vote submission with multi-select (using fake PB service)
# ---------------------------------------------------------------------------

class FakeBehaviorPbService:
    """Stand-in for AsyncPocketBaseService testing vote endpoint behavior."""

    def __init__(self):
        self._polls = {
            "multi_poll": {
                "id": "multi_poll",
                "title": "Pick favorites",
                "owner": "owner-user",
                "max_selections": 3,
                "is_quiz": False,
                "correct_options": None,
                "show_voters": False,
                "result_display": "show_counts",
                "total_votes": 0,
                "close_at": None,
                "options": [
                    {"id": "o1", "text": "Svelte", "vote_count": 0},
                    {"id": "o2", "text": "React", "vote_count": 0},
                    {"id": "o3", "text": "Vue", "vote_count": 0},
                    {"id": "o4", "text": "Angular", "vote_count": 0},
                ],
            },
            "quiz_poll": {
                "id": "quiz_poll",
                "title": "Capital cities",
                "owner": "owner-user",
                "max_selections": 1,
                "is_quiz": True,
                "correct_options": ["o1"],
                "show_voters": False,
                "result_display": "show_counts",
                "total_votes": 5,
                "close_at": None,
                "options": [
                    {"id": "o1", "text": "Paris", "vote_count": 3},
                    {"id": "o2", "text": "London", "vote_count": 2},
                ],
            },
            "single_poll": {
                "id": "single_poll",
                "title": "Pick one",
                "owner": "owner-user",
                "max_selections": 1,
                "is_quiz": False,
                "correct_options": None,
                "show_voters": True,
                "result_display": "show_counts",
                "total_votes": 10,
                "close_at": None,
                "options": [
                    {"id": "o1", "text": "Yes", "vote_count": 7},
                    {"id": "o2", "text": "No", "vote_count": 3},
                ],
            },
        }
        self._votes: list[dict] = []
        self._vote_count = 0

    async def get_poll(self, poll_id):
        return self._polls.get(poll_id)

    async def has_device_voted(self, poll_id, device_token):
        return any(v["poll_id"] == poll_id and v["device_token"] == device_token for v in self._votes)

    async def get_existing_vote(self, poll_id, device_token):
        for v in self._votes:
            if v["poll_id"] == poll_id and v["device_token"] == device_token:
                return v
        return None

    async def cast_vote(self, vote_data):
        self._votes.append(vote_data)
        return {"id": f"vote_{self._vote_count}", **vote_data}

    async def record_vote_and_increment(
        self,
        poll_id,
        vote_data,
        existing_vote_id=None,
        newly_counted_ids=None,
    ):
        poll = self._polls.get(poll_id, {})
        options = poll.get("options", [])
        raw_oid = vote_data["option_id"]
        option_ids = raw_oid if isinstance(raw_oid, list) else [raw_oid]
        increment_ids = option_ids if newly_counted_ids is None else newly_counted_ids
        for oid in increment_ids:
            for opt in options:
                if opt.get("id") == oid:
                    opt["vote_count"] = opt.get("vote_count", 0) + 1
                    break
        self._vote_count += 1
        if existing_vote_id is None:
            # A returning device is not counted toward total_votes a second time
            poll["total_votes"] = poll.get("total_votes", 0) + 1
        else:
            for v in self._votes:
                if v.get("id") == existing_vote_id:
                    v.update(vote_data)
        return {"id": f"vote_{self._vote_count}"}, poll

    async def update_vote(self, vote_id, vote_data):
        for v in self._votes:
            if v.get("id") == vote_id:
                v.update(vote_data)
                return v
        return {"id": vote_id, **vote_data}

    async def list_voters_for_poll(self, poll_id, option_id):
        return []


def _with_fake_behavior_pb():
    fake = FakeBehaviorPbService()
    app.state.pb_service = fake
    return fake


def _clear_fake_behavior_pb():
    if hasattr(app.state, "pb_service"):
        delattr(app.state, "pb_service")


def test_multi_select_vote_success():
    fake = _with_fake_behavior_pb()
    try:
        resp = client.post(
            "/api/v1/votes/multi_poll",
            json={
                "option_id": ["o1", "o2", "o3"],
                "device_token": "device_abc",
            },
            headers={"x-device-token": "device_abc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["selected_options"] == ["o1", "o2", "o3"]
    finally:
        _clear_fake_behavior_pb()


def test_multi_select_exceeds_max_rejected():
    fake = _with_fake_behavior_pb()
    try:
        resp = client.post(
            "/api/v1/votes/multi_poll",
            json={
                "option_id": ["o1", "o2", "o3", "o4"],
                "device_token": "device_xyz",
            },
        )
        assert resp.status_code == 400
        assert "up to 3" in resp.json()["detail"]
    finally:
        _clear_fake_behavior_pb()


def test_single_choice_duplicate_rejected():
    fake = _with_fake_behavior_pb()
    try:
        # Pre-seed a vote
        fake._votes.append({"poll_id": "single_poll", "option_id": "o1", "device_token": "dev_dup"})
        resp = client.post(
            "/api/v1/votes/single_poll",
            json={"option_id": "o2", "device_token": "dev_dup"},
        )
        assert resp.status_code == 400
        assert "already voted" in resp.json()["detail"]
    finally:
        _clear_fake_behavior_pb()


def test_multi_select_duplicate_merge():
    fake = _with_fake_behavior_pb()
    try:
        # Pre-seed a vote with 2 selections
        fake._votes.append({"poll_id": "multi_poll", "option_id": ["o1", "o2"], "device_token": "dev_merge"})
        resp = client.post(
            "/api/v1/votes/multi_poll",
            json={"option_id": ["o2", "o3"], "device_token": "dev_merge"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "o1" in data["selected_options"]
        assert "o2" in data["selected_options"]
        assert "o3" in data["selected_options"]
        assert len(data["selected_options"]) == 3
    finally:
        _clear_fake_behavior_pb()


def test_invalid_option_id_rejected():
    fake = _with_fake_behavior_pb()
    try:
        resp = client.post(
            "/api/v1/votes/multi_poll",
            json={"option_id": ["o1", "fake999"], "device_token": "dev_bad"},
        )
        assert resp.status_code == 400
        assert "Invalid" in resp.json()["detail"]
    finally:
        _clear_fake_behavior_pb()


def test_empty_option_list_rejected():
    from app.schemas.vote import VoteRequest
    import pydantic
    try:
        VoteRequest(option_id=[])
        assert False, "Should raise ValidationError"
    except pydantic.ValidationError:
        pass


def test_duplicate_option_ids_in_list_rejected():
    from app.schemas.vote import VoteRequest
    import pydantic
    try:
        VoteRequest(option_id=["a", "b", "a"])
        assert False, "Should raise ValidationError"
    except pydantic.ValidationError:
        pass


def test_poll_response_max_selections_and_is_quiz():
    """Verify PollResponse serializes behavior fields correctly."""
    from app.schemas.poll import PollResponse, PollOptionResponse
    r = PollResponse(
        id="multi_poll",
        title="Pick favorites",
        options=[PollOptionResponse(id="o1", text="Svelte")],
        visibility="public",
        result_display="show_counts",
        owner="owner-user",
        created="2026-01-01",
        updated="2026-01-01",
        max_selections=3,
        is_quiz=False,
    )
    d = r.model_dump()
    assert d["max_selections"] == 3
    assert d["is_quiz"] is False
    assert d["show_voters"] is False
