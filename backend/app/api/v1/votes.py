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
    Supports single-choice, multi-select, and quiz modes.
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
    cookie_token = request.cookies.get("polls-lab_device_token")
    header_token = request.headers.get("x-device-token")
    device_token = vote.device_token or cookie_token or header_token or str(uuid.uuid4())

    # 4. Normalize option_id to list for uniform handling
    option_ids = vote.option_id if isinstance(vote.option_id, list) else [vote.option_id]

    # 5. Determine poll behavior mode
    max_selections = poll.get("max_selections", 1) or 1
    is_multi = max_selections > 1

    # 6. Check for existing vote — different logic for single vs multi-select
    existing_vote = await pb.get_existing_vote(poll_id, device_token)
    if existing_vote:
        if not is_multi:
            # Single-choice: reject duplicate outright
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already voted on this poll.",
            )
        # Multi-select: get previously selected options for merge/check
        existing_opt = existing_vote.get("option_id", [])
        if isinstance(existing_opt, str):
            existing_opt = [existing_opt]
        # Merge with new selections (deduplicated)
        merged = list(dict.fromkeys(existing_opt + option_ids))
        if len(merged) > max_selections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can select up to {max_selections} option(s). You've selected {len(merged)} total.",
            )
        option_ids = merged

    # 7. Validate option count against max_selections
    if len(option_ids) > max_selections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can select up to {max_selections} option(s). You've selected {len(option_ids)}.",
        )

    # 8. Verify all option IDs exist in the poll
    options = poll.get("options", [])
    option_id_set = {opt.get("id") for opt in options}
    invalid = [oid for oid in option_ids if oid not in option_id_set]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid option(s) selected.",
        )

    # 9. Record Vote and atomically increment counts in PocketBase
    client_ip_hash = hash_ip(client_ip)
    vote_record = {
        "poll_id": poll_id,
        "option_id": option_ids if is_multi else option_ids[0],
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

    # 10. Set httpOnly cookie for voter tracking across embeds
    response.set_cookie(
        key="polls-lab_device_token",
        value=device_token,
        max_age=31536000,  # 1 year
        httponly=True,
        samesite="none",
        secure=True,
    )

    # 11. Apply result display masking so voter responses do not leak counts (PRD §3.2)
    sanitized_options, total_votes = sanitize_poll_options_for_display(
        updated_poll, is_owner=False, is_quiz=poll.get("is_quiz", False),
        correct_options=poll.get("correct_options"), show_voters=poll.get("show_voters", False),
        device_token=device_token, pb=pb,
    )

    return VoteResponse(
        success=True,
        message="Vote recorded successfully",
        poll_id=poll_id,
        device_token=device_token,
        total_votes=total_votes,
        options=sanitized_options,
        selected_options=option_ids,
    )
