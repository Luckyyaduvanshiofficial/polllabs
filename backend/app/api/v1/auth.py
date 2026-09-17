from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from app.core.dependencies import CurrentUser, PocketBaseDep
from app.schemas.auth import GitHubAuthUrlResponse, UserResponse, DeletionStatusResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

class PurgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    purged_count: int
    message: str

@router.get("/github/url", response_model=GitHubAuthUrlResponse)
def get_github_auth_url() -> GitHubAuthUrlResponse:
    """
    Returns GitHub OAuth authorization URL from PocketBase auth methods (PRD §2).
    """
    return GitHubAuthUrlResponse(
        provider="github",
        auth_url="/api/collections/users/auth-with-oauth2",
    )

@router.get("/me", response_model=UserResponse)
def get_current_user(user_id: CurrentUser) -> UserResponse:
    """
    Returns current authenticated user identity.
    """
    return UserResponse(user_id=user_id, provider="github")

@router.post("/delete-account", response_model=DeletionStatusResponse)
async def request_account_deletion(
    user_id: CurrentUser,
    pb: PocketBaseDep,
) -> DeletionStatusResponse:
    """
    Requests account deletion with a 7-day grace period (PRD §7).
    Account is marked pending_deletion; user retains access and can cancel within 7 days.
    """
    grace_period_end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    await pb.set_user_deletion_status(
        user_id=user_id,
        status="pending_deletion",
        scheduled_for=grace_period_end,
    )

    return DeletionStatusResponse(
        status="pending_deletion",
        message="Account scheduled for permanent deletion in 7 days. You may cancel anytime before expiry.",
        grace_period_ends_at=grace_period_end,
    )

@router.post("/cancel-delete-account", response_model=DeletionStatusResponse)
async def cancel_account_deletion(
    user_id: CurrentUser,
    pb: PocketBaseDep,
) -> DeletionStatusResponse:
    """
    Cancels a pending account deletion request within the 7-day grace window (PRD §7).
    """
    await pb.set_user_deletion_status(
        user_id=user_id,
        status="active",
        scheduled_for=None,
    )

    return DeletionStatusResponse(
        status="active",
        message="Account deletion request successfully cancelled. Your account remains active.",
    )

@router.post("/purge-expired-accounts", response_model=PurgeResponse)
async def purge_expired_accounts(pb: PocketBaseDep) -> PurgeResponse:
    """
    Permanently deletes accounts whose 7-day grace period has elapsed,
    triggering cascade deletion of all owned polls and votes (PRD §7).
    """
    purged = await pb.purge_expired_accounts()
    return PurgeResponse(
        purged_count=purged,
        message=f"Successfully purged {purged} expired account(s).",
    )
