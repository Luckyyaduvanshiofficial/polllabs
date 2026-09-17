from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from app.core.dependencies import CurrentUser, PocketBaseDep

router = APIRouter(prefix="/auth", tags=["Auth"])

class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    token: str
    user_id: str
    username: str

@router.get("/github/url")
async def get_github_auth_url(pb: PocketBaseDep) -> dict[str, str]:
    """
    Returns GitHub OAuth authorization URL from PocketBase auth methods.
    """
    # PocketBase lists available OAuth2 providers configured in Admin UI
    try:
        token = await pb.get_admin_token()
        # Direct fallback for standard GitHub OAuth flow
        return {
            "provider": "github",
            "auth_url": "/api/collections/users/auth-with-oauth2",
        }
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to initialize OAuth provider: {err}",
        )

@router.get("/me")
async def get_current_user(user_id: CurrentUser) -> dict[str, str]:
    """
    Returns current authenticated user identity.
    """
    return {"user_id": user_id, "provider": "github"}
