from fastapi import APIRouter, Query
from app.core.dependencies import PocketBaseDep
from app.schemas.leaderboard import (
    LeaderboardResponse,
    MostVotedOptionsResponse,
    MostVotedOptionItem,
)
from app.api.v1.polls import map_poll_to_response

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

async def fetch_leaderboard_polls(
    pb: PocketBaseDep,
    filter_expr: str,
    sort_expr: str,
    limit: int,
) -> LeaderboardResponse:
    """Shared helper deduplicating leaderboard queries and response formatting."""
    result = await pb.list_polls(
        page=1,
        per_page=limit,
        filter_expr=filter_expr,
        sort_expr=sort_expr,
    )
    items = [map_poll_to_response(item) for item in result.get("items", [])]
    return LeaderboardResponse(leaderboard=items, total=len(items))

@router.get("/trending", response_model=LeaderboardResponse)
async def get_trending_polls(
    pb: PocketBaseDep,
    limit: int = Query(default=10, ge=1, le=50),
    min_votes: int = Query(default=3, ge=0),
) -> LeaderboardResponse:
    """
    Returns trending polls based on highest vote counts with engagement thresholds (PRD §3.1, §4.3).
    """
    filter_expr = f'visibility="public" && total_votes >= {min_votes}'
    return await fetch_leaderboard_polls(
        pb=pb,
        filter_expr=filter_expr,
        sort_expr="-total_votes,-created",
        limit=limit,
    )

@router.get("/top", response_model=LeaderboardResponse)
async def get_top_polls(
    pb: PocketBaseDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> LeaderboardResponse:
    """
    Returns all-time top voted public polls (PRD §4.3).
    """
    return await fetch_leaderboard_polls(
        pb=pb,
        filter_expr='visibility="public"',
        sort_expr="-total_votes",
        limit=limit,
    )

@router.get("/most-voted-options", response_model=MostVotedOptionsResponse)
async def get_most_voted_options(
    pb: PocketBaseDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> MostVotedOptionsResponse:
    """
    Surfaces the most-voted options across public polls (PRD §4.3: 'most-voted options').
    """
    result = await pb.list_polls(
        page=1,
        per_page=50,
        filter_expr='visibility="public"',
        sort_expr="-total_votes",
    )

    all_options: list[MostVotedOptionItem] = []
    for poll in result.get("items", []):
        for opt in poll.get("options", []):
            if opt.get("vote_count", 0) > 0:
                all_options.append(
                    MostVotedOptionItem(
                        poll_id=poll["id"],
                        poll_title=poll["title"],
                        option_id=opt["id"],
                        option_text=opt.get("text", opt["id"]),
                        vote_count=opt.get("vote_count", 0),
                    )
                )

    all_options.sort(key=lambda x: x.vote_count, reverse=True)
    top_options = all_options[:limit]

    return MostVotedOptionsResponse(items=top_options, total=len(top_options))
