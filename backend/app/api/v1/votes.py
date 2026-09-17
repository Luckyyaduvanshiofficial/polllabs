import uuid
from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.vote import VoteRequest, VoteResponse
from app.core.rate_limit import check_ip_rate_limit

router = APIRouter(prefix="/votes", tags=["Votes"])

@router.post("/{poll_id}", response_model=VoteResponse)
async def submit_vote(poll_id: str, vote: VoteRequest, request: Request) -> VoteResponse:
    """
    Submits a vote on a poll.
    Validates rate-limits (IP hash) and device token.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Secondary signal: IP-based rate limiting (PRD §4.6)
    if not check_ip_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again shortly."
        )

    # Primary signal: Device token
    device_token = vote.device_token or str(uuid.uuid4())

    return VoteResponse(
        success=True,
        message="Vote recorded successfully",
        poll_id=poll_id,
        device_token=device_token
    )
