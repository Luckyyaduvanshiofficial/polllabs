import base64
import json
import logging
from typing import Annotated
from fastapi import Depends, HTTPException, Header, status
from app.core.config import settings
from app.services.pocketbase_service import AsyncPocketBaseService, get_pb_service

logger = logging.getLogger("polllabs.auth")

# Type aliases using Annotated per FastAPI best practices
PocketBaseDep = Annotated[AsyncPocketBaseService, Depends(get_pb_service)]

def extract_user_id_from_token(token: str) -> str:
    """Extracts user ID from PocketBase JWT token payload if formatted as JWT."""
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            # PocketBase JWT payload
            padding = "=" * ((4 - len(parts[1]) % 4) % 4)
            payload_bytes = base64.urlsafe_b64decode(parts[1] + padding)
            payload = json.loads(payload_bytes.decode("utf-8"))
            return payload.get("id") or payload.get("sub") or token
    except Exception as err:
        logger.debug("Failed parsing JWT token payload: %s", err)
    return token

async def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None),
) -> str:
    """
    Extracts authenticated user ID from Authorization header.
    In production mode, x-dev-user-id header is strictly rejected per security policy.
    """
    if x_dev_user_id:
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Development authorization headers are forbidden in production.",
            )
        return x_dev_user_id

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in with GitHub.",
        )

    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token format.",
        )

    return extract_user_id_from_token(token)

async def get_optional_user_id(
    authorization: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None),
) -> str | None:
    """
    Optionally extracts authenticated user ID without raising 401 when unauthenticated.
    Enables owner unmasking on public endpoints (PRD §3.2).
    """
    try:
        return await get_current_user_id(authorization, x_dev_user_id)
    except HTTPException:
        return None

CurrentUser = Annotated[str, Depends(get_current_user_id)]
OptionalUser = Annotated[str | None, Depends(get_optional_user_id)]
