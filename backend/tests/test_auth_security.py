"""Regression tests for auth verification.

These deliberately do NOT use the auth overrides in conftest: they exercise the
real dependency, because the bug they guard against was that the dependency
trusted the JWT payload without verifying it.
"""

import base64
import json

import pytest
from fastapi import HTTPException

from app.core import dependencies
from app.core.config import Settings
from app.core.dependencies import get_current_user_id, verify_admin_key


class StubPb:
    """PocketBase stand-in: only `valid-token` is a real session."""

    def __init__(self):
        self.seen: list[str] = []

    async def verify_user_token(self, token: str) -> str | None:
        self.seen.append(token)
        return "real_user_id" if token == "valid-token" else None


def _forged_jwt(user_id: str) -> str:
    def seg(payload: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    return f"{seg({'alg': 'none'})}.{seg({'id': user_id})}.not_a_signature"


@pytest.mark.asyncio
async def test_forged_unsigned_token_is_rejected():
    """A JWT-shaped token with an arbitrary id must not establish identity."""
    pb = StubPb()
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(
            pb,
            authorization=f"Bearer {_forged_jwt('victim_user')}",
            x_dev_user_id=None,
        )
    assert exc.value.status_code == 401
    # The token was checked against PocketBase rather than decoded locally.
    assert pb.seen == [_forged_jwt("victim_user")]


@pytest.mark.asyncio
async def test_valid_token_resolves_to_pocketbase_identity():
    """The id comes from PocketBase, never from the client-supplied payload."""
    pb = StubPb()
    user_id = await get_current_user_id(
        pb, authorization="Bearer valid-token", x_dev_user_id=None
    )
    assert user_id == "real_user_id"


@pytest.mark.asyncio
async def test_forged_payload_cannot_override_verified_identity():
    """Even a well-formed payload claiming another user resolves to the real one."""
    pb = StubPb()
    with pytest.raises(HTTPException):
        await get_current_user_id(
            pb,
            authorization=f"Bearer {_forged_jwt('real_user_id')}",
            x_dev_user_id=None,
        )


@pytest.mark.asyncio
async def test_missing_credentials_rejected():
    pb = StubPb()
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(pb, authorization=None, x_dev_user_id=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_dev_header_rejected_when_not_enabled(monkeypatch):
    """x-dev-user-id must not grant identity unless explicitly enabled."""
    monkeypatch.setattr(dependencies, "_DEV_AUTH_ALLOWED", False)
    pb = StubPb()
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(pb, x_dev_user_id="anyone")
    assert exc.value.status_code == 401


def test_admin_key_disabled_when_unset(monkeypatch):
    """With no ADMIN_API_KEY there is no fallback constant to guess."""
    monkeypatch.setattr(dependencies.settings, "ADMIN_API_KEY", "")
    for candidate in (None, "polls-lab-admin-secret", "anything"):
        with pytest.raises(HTTPException) as exc:
            verify_admin_key(x_admin_key=candidate)
        assert exc.value.status_code == 403


def test_admin_key_requires_exact_match(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "ADMIN_API_KEY", "s3cret")
    assert verify_admin_key(x_admin_key="s3cret") == "s3cret"
    with pytest.raises(HTTPException):
        verify_admin_key(x_admin_key="wrong")


def test_production_refuses_missing_secrets():
    """Startup fails closed rather than falling back to published constants."""
    with pytest.raises(ValueError) as exc:
        Settings(_env_file=None, ENVIRONMENT="production")
    message = str(exc.value)
    assert "IP_HASH_SALT" in message and "ADMIN_API_KEY" in message


def test_production_refuses_dev_auth_headers():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            IP_HASH_SALT="x" * 32,
            ADMIN_API_KEY="y" * 32,
            ALLOW_DEV_AUTH_HEADERS=True,
        )


def test_development_salt_is_not_a_published_constant():
    settings = Settings(_env_file=None)
    assert settings.IP_HASH_SALT
    assert settings.IP_HASH_SALT != "change-in-production-salt"
    assert len(settings.IP_HASH_SALT) >= 32
