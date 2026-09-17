import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.poll import PollCreate, PollResponse, PollOptionBase
from app.core.dependencies import CurrentUser, PocketBaseDep
from app.services.moderation import validate_content_safety

router = APIRouter(prefix="/polls", tags=["Polls"])

def sanitize_poll_options_for_display(poll_data: dict) -> list[dict]:
    """Applies PRD §3.2 result display rules (show_counts, show_percentage, hidden_until_close)."""
    options = poll_data.get("options", [])
    total_votes = poll_data.get("total_votes", 0)
    result_display = poll_data.get("result_display", "show_counts")
    close_at = poll_data.get("close_at")

    is_closed = False
    if close_at:
        try:
            close_time = datetime.fromisoformat(close_at.replace("Z", "+00:00"))
            is_closed = datetime.now(timezone.utc) >= close_time
        except Exception:
            pass

    sanitized = []
    for opt in options:
        opt_copy = dict(opt)
        count = opt.get("vote_count", 0)
        percentage = round((count / total_votes * 100), 1) if total_votes > 0 else 0.0

        if result_display == "hidden_until_close" and not is_closed:
            opt_copy["vote_count"] = -1  # Indicates hidden
            opt_copy["percentage"] = None
        elif result_display == "show_percentage":
            opt_copy["vote_count"] = -1
            opt_copy["percentage"] = percentage
        else:  # show_counts
            opt_copy["percentage"] = percentage

        sanitized.append(opt_copy)

    return sanitized

@router.get("/", response_model=dict)
async def list_public_polls(
    pb: PocketBaseDep,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="-created"),
) -> dict:
    """Lists discoverable public polls with pagination."""
    result = await pb.list_polls(
        page=page,
        per_page=per_page,
        filter_expr='visibility="public"',
        sort_expr=sort,
    )
    items = result.get("items", [])
    for item in items:
        item["options"] = sanitize_poll_options_for_display(item)

    return {
        "items": items,
        "page": result.get("page", 1),
        "per_page": result.get("perPage", per_page),
        "total_items": result.get("totalItems", 0),
        "total_pages": result.get("totalPages", 1),
    }

@router.get("/{poll_id}", response_model=dict)
async def get_poll(poll_id: str, pb: PocketBaseDep) -> dict:
    """Retrieves a single poll by ID, applying result display rules."""
    poll = await pb.get_poll(poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found or is no longer available.",
        )

    poll["options"] = sanitize_poll_options_for_display(poll)
    return poll

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_poll(
    poll_in: PollCreate,
    owner_id: CurrentUser,
    pb: PocketBaseDep,
) -> dict:
    """Creates a new poll. Requires GitHub authentication and passes content moderation."""
    # 1. Content Moderation
    is_safe, reason = validate_content_safety(poll_in.title)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Title moderation failed: {reason}",
        )

    structured_options = []
    for opt_text in poll_in.options:
        opt_safe, opt_reason = validate_content_safety(opt_text)
        if not opt_safe:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Option moderation failed: {opt_reason}",
            )
        structured_options.append({
            "id": str(uuid.uuid4())[:8],
            "text": opt_text.strip(),
            "vote_count": 0,
        })

    # 2. Persist to PocketBase
    poll_record = {
        "title": poll_in.title.strip(),
        "description": poll_in.description.strip() if poll_in.description else "",
        "options": structured_options,
        "visibility": poll_in.visibility,
        "result_display": poll_in.result_display,
        "close_at": poll_in.close_at,
        "owner": owner_id,
        "total_votes": 0,
    }

    try:
        created = await pb.create_poll(poll_record)
        return {
            "id": created.get("id"),
            "title": created.get("title"),
            "visibility": created.get("visibility"),
            "message": "Poll created successfully",
        }
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create poll: {err}",
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
