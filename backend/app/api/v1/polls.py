import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Query, Request, status
from app.schemas.poll import (
    PollCreate,
    PollUpdate,
    PollResponse,
    PollListResponse,
    PollOptionResponse,
    PollReportRequest,
    PollReportResponse,
)
from app.core.dependencies import CurrentUser, OptionalUser, PocketBaseDep
from app.core.rate_limit import hash_ip
from app.services.moderation import validate_content_safety
from app.services.poll_utils import coerce_appearance, is_poll_closed

router = APIRouter(prefix="/polls", tags=["Polls"])

def sanitize_poll_options_for_display(
    poll_data: dict[str, Any],
    is_owner: bool = False,
) -> tuple[list[PollOptionResponse], int | None]:
    """
    Applies PRD §3.2 result display rules (show_counts, show_percentage, hidden_until_close).
    Returns sanitized option list and masked/unmasked total_votes counter.
    Owners always see full results in the dashboard.
    """
    options = poll_data.get("options", [])
    raw_total = poll_data.get("total_votes", 0)
    result_display = poll_data.get("result_display", "show_counts")
    closed = is_poll_closed(poll_data.get("close_at"))

    sanitized: list[PollOptionResponse] = []
    display_total_votes: int | None = raw_total

    for opt in options:
        opt_dict = dict(opt)
        count = opt_dict.get("vote_count", 0)
        percentage = round((count / raw_total * 100), 1) if raw_total > 0 else 0.0

        if is_owner:
            # PRD §3.2: Owner always sees full results in dashboard
            display_count = count
            display_pct = percentage
        elif result_display == "hidden_until_close" and not closed:
            # PRD §3.2: No results shown to voters until close time
            display_count = None
            display_pct = None
            display_total_votes = None
        elif result_display == "show_percentage":
            # PRD §3.2: Only percentages shown, no raw counts (total_votes is also masked)
            display_count = None
            display_pct = percentage
            display_total_votes = None
        else:  # show_counts or closed hidden poll
            display_count = count
            display_pct = percentage

        sanitized.append(
            PollOptionResponse(
                id=opt_dict["id"],
                text=opt_dict["text"],
                icon_or_image=opt_dict.get("icon_or_image"),
                vote_count=display_count,
                percentage=display_pct,
            )
        )

    # Double check total_votes masking when not owner
    if not is_owner:
        if result_display == "show_percentage" or (result_display == "hidden_until_close" and not closed):
            display_total_votes = None

    return sanitized, display_total_votes

def map_poll_to_response(poll: dict[str, Any], is_owner: bool = False) -> PollResponse:
    """Transforms raw PocketBase dictionary to strongly-typed PollResponse model."""
    sanitized_options, total_votes = sanitize_poll_options_for_display(poll, is_owner=is_owner)
    return PollResponse(
        id=poll["id"],
        title=poll["title"],
        description=poll.get("description"),
        options=sanitized_options,
        visibility=poll.get("visibility", "public"),
        result_display=poll.get("result_display", "show_counts"),
        owner=poll.get("owner", ""),
        total_votes=total_votes,
        created=poll.get("created", ""),
        updated=poll.get("updated", ""),
        close_at=poll.get("close_at"),
        appearance=coerce_appearance(poll.get("appearance")),
    )

@router.get("", response_model=PollListResponse)
@router.get("/", response_model=PollListResponse)
async def list_public_polls(
    pb: PocketBaseDep,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="-created"),
) -> PollListResponse:
    """Lists discoverable public polls with pagination."""
    result = await pb.list_polls(
        page=page,
        per_page=per_page,
        filter_expr='visibility="public"',
        sort_expr=sort,
    )
    raw_items = result.get("items", [])
    items = [map_poll_to_response(item, is_owner=False) for item in raw_items]

    return PollListResponse(
        items=items,
        page=result.get("page", 1),
        per_page=result.get("perPage", per_page),
        total_items=result.get("totalItems", len(items)),
        total_pages=result.get("totalPages", 1),
    )

@router.get("/{poll_id}", response_model=PollResponse)
async def get_poll(
    poll_id: str,
    pb: PocketBaseDep,
    current_user_id: OptionalUser = None,
) -> PollResponse:
    """
    Retrieves a single poll by ID.
    Unmasks full results if the requester is the authenticated owner (PRD §3.2).
    """
    poll = await pb.get_poll(poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This poll is no longer available.",
        )

    is_owner = bool(current_user_id and current_user_id == poll.get("owner"))
    return map_poll_to_response(poll, is_owner=is_owner)

@router.post("", response_model=PollResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PollResponse, status_code=status.HTTP_201_CREATED)
async def create_poll(
    poll_in: PollCreate,
    owner_id: CurrentUser,
    pb: PocketBaseDep,
) -> PollResponse:
    """
    Creates a new poll.
    Requires GitHub authentication and passes content moderation (PRD §4.1, §4.6).
    """
    # Content moderation on title
    is_safe, reason = validate_content_safety(poll_in.title)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Title moderation failed: {reason}",
        )

    structured_options = []
    for opt in poll_in.options:
        text = opt.text if hasattr(opt, "text") else str(opt)
        icon_or_image = opt.icon_or_image if hasattr(opt, "icon_or_image") else None

        opt_safe, opt_reason = validate_content_safety(text)
        if not opt_safe:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Option moderation failed: {opt_reason}",
            )
        structured_options.append({
            "id": str(uuid.uuid4())[:8],
            "text": text.strip(),
            "icon_or_image": icon_or_image,
            "vote_count": 0,
        })

    close_at_val = None
    if poll_in.close_at:
        close_at_val = poll_in.close_at.isoformat() if hasattr(poll_in.close_at, "isoformat") else str(poll_in.close_at)

    poll_record = {
        "title": poll_in.title.strip(),
        "description": poll_in.description.strip() if poll_in.description else "",
        "options": structured_options,
        "visibility": poll_in.visibility,
        "result_display": poll_in.result_display,
        "close_at": close_at_val,
        "owner": owner_id,
        "total_votes": 0,
        "appearance": poll_in.appearance.model_dump(exclude_none=True) if poll_in.appearance else {},
    }

    try:
        created = await pb.create_poll(poll_record)
        return map_poll_to_response(created, is_owner=True)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create poll: {err}",
        )

@router.patch("/{poll_id}", response_model=PollResponse)
async def update_poll(
    poll_id: str,
    poll_update: PollUpdate,
    user_id: CurrentUser,
    pb: PocketBaseDep,
) -> PollResponse:
    """
    Updates poll settings. Owner only (PRD §4.1: 'Owner can edit or delete their poll at any time').
    """
    poll = await pb.get_poll(poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found.",
        )

    if poll.get("owner") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to edit this poll.",
        )

    update_dict: dict[str, Any] = {}
    if poll_update.title is not None:
        is_safe, reason = validate_content_safety(poll_update.title)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Title moderation failed: {reason}",
            )
        update_dict["title"] = poll_update.title.strip()

    if poll_update.description is not None:
        update_dict["description"] = poll_update.description.strip()
    if poll_update.visibility is not None:
        update_dict["visibility"] = poll_update.visibility
    if poll_update.result_display is not None:
        update_dict["result_display"] = poll_update.result_display
    if poll_update.close_at is not None:
        close_val = poll_update.close_at.isoformat() if hasattr(poll_update.close_at, "isoformat") else str(poll_update.close_at)
        update_dict["close_at"] = close_val
    if poll_update.appearance is not None:
        update_dict["appearance"] = poll_update.appearance.model_dump(exclude_none=True)

    try:
        updated = await pb.update_poll(poll_id, update_dict)
        return map_poll_to_response(updated, is_owner=True)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update poll: {err}",
        )

@router.delete("/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_poll(
    poll_id: str,
    user_id: CurrentUser,
    pb: PocketBaseDep,
) -> None:
    """Deletes a poll. Owner only. Associated votes are cascade deleted automatically."""
    poll = await pb.get_poll(poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found.",
        )

    if poll.get("owner") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this poll.",
        )

    success = await pb.delete_poll(poll_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete poll.",
        )

@router.post("/{poll_id}/report", response_model=PollReportResponse)
async def report_poll_abuse(
    poll_id: str,
    report: PollReportRequest,
    request: Request,
    pb: PocketBaseDep,
) -> PollReportResponse:
    """
    Report-abuse action on public polls (PRD §4.6). Persists reports to PocketBase.
    """
    poll = await pb.get_poll(poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found.",
        )

    client_ip = request.client.host if request.client else "127.0.0.1"
    reporter_ip_hash = hash_ip(client_ip)

    await pb.record_abuse_report(
        poll_id=poll_id,
        reason=report.reason,
        ip_hash=reporter_ip_hash,
    )

    return PollReportResponse(
        status="reported",
        poll_id=poll_id,
        message="Thank you for your report. Our moderators will review this content.",
    )
