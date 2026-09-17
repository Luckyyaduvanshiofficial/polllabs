from fastapi import APIRouter, Query
from app.core.dependencies import PocketBaseDep
from app.api.v1.polls import sanitize_poll_options_for_display

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/trending", response_model=dict)
async def get_trending_polls(
    pb: PocketBaseDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    """
    Returns trending polls based on highest vote counts (filtered to public polls per PRD §4.3).
    """
    result = await pb.list_polls(
        page=1,
        per_page=limit,
        filter_expr='visibility="public"',
        sort_expr="-total_votes,-created",
    )
    items = result.get("items", [])
    for item in items:
        item["options"] = sanitize_poll_options_for_display(item)

    return {
        "leaderboard": items,
        "total": len(items),
    }

@router.get("/recent", response_model=dict)
async def get_recent_polls(
    pb: PocketBaseDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    """
    Returns newest public polls on the platform.
    """
    result = await pb.list_polls(
        page=1,
        per_page=limit,
        filter_expr='visibility="public"',
        sort_expr="-created",
    )
    items = result.get("items", [])
    for item in items:
        item["options"] = sanitize_poll_options_for_display(item)

    return {
        "recent": items,
        "total": len(items),
    }
