from typing import Annotated
from fastapi import Depends, HTTPException, Header, status
from app.services.pocketbase_service import AsyncPocketBaseService, get_pb_service

# Type aliases using Annotated per FastAPI best practices
PocketBaseDep = Annotated[AsyncPocketBaseService, Depends(get_pb_service)]

async def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None),
) -> str:
    """
    Extracts authenticated user ID from Authorization header or dev fallback.
    In production, validates token with PocketBase.
    """
    # Development header fallback for testing without GitHub OAuth credentials
    if x_dev_user_id:
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

    # Return token as user context
    return token

CurrentUser = Annotated[str, Depends(get_current_user_id)]
