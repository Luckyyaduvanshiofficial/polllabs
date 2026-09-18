import logging
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings
from app.services.pocketbase_service import AsyncPocketBaseService, get_pb_service

logger = logging.getLogger("polls-lab.auth")

# Type aliases using Annotated per FastAPI best practices
PocketBaseDep = Annotated[AsyncPocketBaseService, Depends(get_pb_service)]

_DEV_AUTH_ALLOWED = not settings.is_production and settings.ALLOW_DEV_AUTH_HEADERS


def _bearer_token(authorization: str | None) -> str:
    """Extracts the bare token from an Authorization header value."""
    if not authorization:
        return ""
    value = authorization.strip()
    if value.lower().startswith("bearer "):
        value = value[7:]
    return value.strip()


async def get_current_user_id(
    pb: PocketBaseDep,
    authorization: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None),
) -> str:
    """
    Resolves the authenticated user id by verifying the token with PocketBase.

    The token payload is never trusted on its own: PocketBase validates the
    signature and expiry, so a forged or unsigned JWT cannot claim an identity
    (PRD §2). The x-dev-user-id shortcut requires ALLOW_DEV_AUTH_HEADERS and is
    unavailable in production.
    """
    if x_dev_user_id:
        if not _DEV_AUTH_ALLOWED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Development authorization headers are not enabled.",
            )
        return x_dev_user_id

    token = _bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in with GitHub.",
        )

    user_id = await pb.verify_user_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )
    return user_id


async def get_optional_user_id(
    pb: PocketBaseDep,
    authorization: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None),
) -> str | None:
    """
    Resolves the user id when credentials are present and valid, else None.
    Enables owner unmasking on public endpoints (PRD §3.2) without forcing auth.
    """
    if not authorization and not x_dev_user_id:
        return None
    try:
        return await get_current_user_id(pb, authorization, x_dev_user_id)
    except HTTPException:
        return None


CurrentUser = Annotated[str, Depends(get_current_user_id)]
OptionalUser = Annotated[str | None, Depends(get_optional_user_id)]


def verify_admin_key(
    x_admin_key: str | None = Header(default=None),
) -> str:
    """
    Restricts administrative endpoints to holders of ADMIN_API_KEY.

    There is no fallback key: when ADMIN_API_KEY is unset every request is
    refused, so an unconfigured deploy cannot be driven with a published
    constant. Compared in constant time.
    """
    expected_key = settings.ADMIN_API_KEY.strip()
    if not expected_key:
        logger.warning("ADMIN_API_KEY is unset; administrative endpoints are disabled.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative endpoints are not configured.",
        )
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative authorization required.",
        )
    return x_admin_key


AdminAuth = Annotated[str, Depends(verify_admin_key)]
