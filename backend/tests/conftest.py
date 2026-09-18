"""Shared test setup.

Endpoint tests exercise handler behaviour, not the auth handshake, so the auth
dependencies are overridden here to treat the bearer token as the user id — the
semantics the suite was written against. Real token verification is covered
directly in tests/test_auth_security.py, which does not use these overrides.
"""

import pytest
from fastapi import Header, HTTPException, status

from app.core.config import settings
from app.core.dependencies import get_current_user_id, get_optional_user_id
from app.main import app

TEST_ADMIN_KEY = "test-admin-key"


async def _stub_current_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in with GitHub.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token format.",
        )
    return token


async def _stub_optional_user(authorization: str | None = Header(default=None)) -> str | None:
    if not authorization:
        return None
    return authorization.removeprefix("Bearer ").strip() or None


@pytest.fixture(autouse=True)
def override_auth():
    """Applies the stub auth resolvers and a known admin key for every test."""
    original_admin_key = settings.ADMIN_API_KEY
    settings.ADMIN_API_KEY = TEST_ADMIN_KEY
    app.dependency_overrides[get_current_user_id] = _stub_current_user
    app.dependency_overrides[get_optional_user_id] = _stub_optional_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
        app.dependency_overrides.pop(get_optional_user_id, None)
        settings.ADMIN_API_KEY = original_admin_key
