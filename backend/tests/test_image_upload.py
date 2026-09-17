from fastapi.testclient import TestClient
from app.main import app
from app.services.image_upload import (
    MAX_IMAGE_BYTES,
    build_file_url,
    detect_image_mime,
    sanitize_filename,
)

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-token-123"}


def test_detect_image_mime():
    assert detect_image_mime(bytes.fromhex("FFD8FFE000104A46")) == "image/jpeg"
    assert detect_image_mime(b"\x89PNG\r\n\x1a\nrest") == "image/png"
    assert detect_image_mime(b"GIF89a rest") == "image/gif"
    assert detect_image_mime(b"RIFF1234WEBP rest") == "image/webp"
    assert detect_image_mime(b"not an image at all") is None
    assert detect_image_mime(b"") is None
    assert detect_image_mime(b"RIFF1234JPEG rest") is None


def test_sanitize_filename():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("my thumb (1).PNG") == "my_thumb__1_.PNG"
    assert sanitize_filename(None) == "upload"
    assert len(sanitize_filename("a" * 200 + ".png")) <= 100


def test_build_file_url():
    url = build_file_url("poll_images", "abc123", "thumb.png")
    assert url.startswith("http")
    assert "/api/files/poll_images/abc123/thumb.png" in url


def test_upload_requires_auth():
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    response = client.post("/api/v1/polls/images", files={"file": ("t.png", png, "image/png")})
    assert response.status_code == 401


def test_upload_rejects_non_image():
    response = client.post(
        "/api/v1/polls/images",
        headers=AUTH,
        files={"file": ("evil.txt", b"not an image at all", "text/plain")},
    )
    assert response.status_code == 400
    assert "JPEG" in response.json()["detail"]


def test_upload_rejects_oversize():
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (MAX_IMAGE_BYTES + 1)
    response = client.post(
        "/api/v1/polls/images",
        headers=AUTH,
        files={"file": ("big.png", big, "image/png")},
    )
    assert response.status_code == 400
    assert "2MB" in response.json()["detail"]


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


class FakePbService:
    """Stand-in for AsyncPocketBaseService: no live PocketBase needed."""

    def __init__(self):
        self.created_payloads: list[dict] = []

    async def get_poll(self, poll_id: str):
        if poll_id == "owned123":
            return {"id": "owned123", "owner": "test-token-123"}
        if poll_id == "foreign123":
            return {"id": "foreign123", "owner": "someone-else"}
        return None

    async def upload_image_record(self, data, filename, content, content_type):
        self.created_payloads.append(data)
        return {"id": "img123", "image": filename}

    async def list_image_records_older_than(self, cutoff_iso, per_page=100):
        return []

    async def delete_image_record(self, record_id):
        return True


def _with_fake_pb():
    fake = FakePbService()
    app.state.pb_service = fake
    return fake


def _clear_fake_pb():
    if hasattr(app.state, "pb_service"):
        delattr(app.state, "pb_service")


def test_upload_staged_201():
    fake = _with_fake_pb()
    try:
        response = client.post(
            "/api/v1/polls/images",
            headers=AUTH,
            files={"file": ("thumb.png", PNG_BYTES, "image/png")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "img123"
        assert "/api/files/poll_images/img123/thumb.png" in data["url"]
        assert "poll_id" not in fake.created_payloads[0]
        assert fake.created_payloads[0]["owner"] == "test-token-123"
    finally:
        _clear_fake_pb()


def test_upload_attached_to_owned_poll():
    fake = _with_fake_pb()
    try:
        response = client.post(
            "/api/v1/polls/images",
            headers=AUTH,
            files={"file": ("thumb.png", PNG_BYTES, "image/png")},
            data={"poll_id": "owned123"},
        )
        assert response.status_code == 201
        assert fake.created_payloads[0]["poll_id"] == "owned123"
    finally:
        _clear_fake_pb()


def test_upload_rejects_missing_and_foreign_poll():
    _with_fake_pb()
    try:
        missing = client.post(
            "/api/v1/polls/images",
            headers=AUTH,
            files={"file": ("thumb.png", PNG_BYTES, "image/png")},
            data={"poll_id": "ghost999"},
        )
        assert missing.status_code == 404

        foreign = client.post(
            "/api/v1/polls/images",
            headers=AUTH,
            files={"file": ("thumb.png", PNG_BYTES, "image/png")},
            data={"poll_id": "foreign123"},
        )
        assert foreign.status_code == 403
    finally:
        _clear_fake_pb()
