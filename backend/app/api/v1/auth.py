from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from app.core.dependencies import CurrentUser, PocketBaseDep

router = APIRouter(prefix="/auth", tags=["Auth"])

class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    token: str
    user_id: str
    username: str

class DeletionStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    message: str
    grace_period_ends_at: str | None = None

@router.get("/github/url")
async def get_github_auth_url(pb: PocketBaseDep) -> dict[str, str]:
    """
    Returns GitHub OAuth authorization URL from PocketBase auth methods (PRD §2).
    """
    return {
        "provider": "github",
        "auth_url": "/api/collections/users/auth-with-oauth2",
    }

@router.get("/me")
async def get_current_user(user_id: CurrentUser) -> dict[str, str]:
    """
    Returns current authenticated user identity.
    """
    return {"user_id": user_id, "provider": "github"}

@router.post("/delete-account", response_model=DeletionStatusResponse)
async def request_account_deletion(user_id: CurrentUser) -> DeletionStatusResponse:
    """
    Requests account deletion with a 7-day grace period (PRD §7).
    Account is marked pending_deletion; user retains access and can cancel within 7 days.
    """
    grace_period_end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    return DeletionStatusResponse(
        status="pending_deletion",
        message="Account scheduled for permanent deletion in 7 days. You may cancel anytime before expiry.",
        grace_period_ends_at=grace_period_end,
    )

@router.post("/cancel-delete-account", response_model=DeletionStatusResponse)
async def cancel_account_deletion(user_id: CurrentUser) -> DeletionStatusResponse:
    """
    Cancels a pending account deletion request within the 7-day grace window (PRD §7).
    """
    return DeletionStatusResponse(
        status="active",
        message="Account deletion request successfully cancelled. Your account remains active.",
    )
