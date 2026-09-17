import uuid
from fastapi import APIRouter, HTTPException, Request, Response, status
from app.schemas.vote import VoteRequest, VoteResponse
from app.core.rate_limit import check_ip_rate_limit, hash_ip
from app.core.dependencies import PocketBaseDep
from app.api.v1.polls import sanitize_poll_options_for_display
from app.services.poll_utils import is_poll_closed

router = APIRouter(prefix="/votes", tags=["Votes"])

@router.post("/{poll_id}", response_model=VoteResponse)
async def submit_vote(
    poll_id: str,
    vote: VoteRequest,
    request: Request,
    response: Response,
    pb: PocketBaseDep,
) -> VoteResponse:
    """
    Submits an anonymous vote on a poll.
    Enforces device-token check, localStorage fallback, and IP-hash rate limiting per PRD §4.6.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    # 1. Secondary Signal: IP-based rate limiting
    if not check_ip_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a minute before voting again.",
        )

    # 2. Verify Poll exists and is active
    poll = await pb.get_poll(poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This poll is no longer available.",
        )

    # Check expiration date using deduplicated helper
    if is_poll_closed(poll.get("close_at")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This poll is closed and no longer accepting votes.",
        )

    # 3. Primary Signal: Device Token (Cookie, Header, or LocalStorage payload)
    cookie_token = request.cookies.get("polllabs_device_token")
    header_token = request.headers.get("x-device-token")
    device_token = vote.device_token or cookie_token or header_token or str(uuid.uuid4())

    # Check for duplicate vote by this device token
    has_voted = await pb.has_device_voted(poll_id, device_token)
    if has_voted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already voted on this poll.",
        )

    # 4. Verify Option exists
    options = poll.get("options", [])
    matched_option = next((opt for opt in options if opt.get("id") == vote.option_id), None)
    if not matched_option:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid option selected.",
        )

    # 5. Record Vote and atomically increment counts in PocketBase
    client_ip_hash = hash_ip(client_ip)
    vote_record = {
        "poll_id": poll_id,
        "option_id": vote.option_id,
        "device_token": device_token,
        "ip_hash": client_ip_hash,
        "embed_referrer": vote.embed_referrer or request.headers.get("referer", ""),
    }

    try:
        _, updated_poll = await pb.record_vote_and_increment(poll_id, vote_record)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record vote: {err}",
        )

    # 6. Set httpOnly cookie for voter tracking across embeds
    response.set_cookie(
        key="polllabs_device_token",
        value=device_token,
        max_age=31536000,  # 1 year
        httponly=True,
        samesite="none",
        secure=True,
    )

    # 7. Apply result display masking so voter responses do not leak counts (PRD §3.2)
    sanitized_options, total_votes = sanitize_poll_options_for_display(updated_poll, is_owner=False)

    return VoteResponse(
        success=True,
        message="Vote recorded successfully",
        poll_id=poll_id,
        device_token=device_token,
        total_votes=total_votes,
        options=sanitized_options,
    )
