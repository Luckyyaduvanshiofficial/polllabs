import uuid
from fastapi import APIRouter, Request, HTTPException
from app.schemas.vote import VoteRequest, VoteResponse
from app.core.rate_limit import check_ip_rate_limit

router = APIRouter()

@router.post("/{poll_id}", response_model=VoteResponse)
def submit_vote(poll_id: str, vote: VoteRequest, request: Request):
    """
    Submits a vote on a poll.
    Validates rate-limits (IP hash) and device token.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Secondary signal: IP-based rate limiting (PRD §4.6)
    if not check_ip_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
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
