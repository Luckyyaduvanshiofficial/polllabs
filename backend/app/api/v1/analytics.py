import csv
import io
import json
from collections import Counter
from fastapi import APIRouter, HTTPException, Response, status
from app.core.dependencies import CurrentUser, PocketBaseDep
from app.schemas.analytics import AnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/{poll_id}", response_model=AnalyticsResponse)
async def get_poll_analytics(
    poll_id: str,
    user_id: CurrentUser,
    pb: PocketBaseDep,
) -> AnalyticsResponse:
    """
    Returns owner-only poll analytics including vote timelines,
    option breakdowns, and embed referrers (PRD §4.3).
    """
    poll = await pb.get_poll(poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found.",
        )

    # Owner-only authorization guard clause
    if poll.get("owner") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view analytics for polls you own.",
        )

    votes = await pb.list_votes_for_poll(poll_id)

    # Breakdown by referrer site
    referrer_counts = Counter(
        v.get("embed_referrer") or "Direct Link" for v in votes
    )

    # Breakdown by option
    option_map = {opt["id"]: opt.get("text", opt["id"]) for opt in poll.get("options", [])}
    option_counts = Counter(
        option_map.get(v.get("option_id"), "Unknown") for v in votes
    )

    # Timeline breakdown (votes over time, grouped by date YYYY-MM-DD)
    time_series = Counter(
        (v.get("created", "")[:10] if v.get("created") else "Unknown")
        for v in votes
    )

    return AnalyticsResponse(
        poll_id=poll_id,
        title=poll.get("title", ""),
        total_votes=len(votes),
        options_breakdown=dict(option_counts),
        referrers_breakdown=dict(referrer_counts),
        votes_over_time=dict(sorted(time_series.items())),
    )

@router.get("/{poll_id}/export")
async def export_poll_data(
    poll_id: str,
    user_id: CurrentUser,
    pb: PocketBaseDep,
    format: str = "json",
) -> Response:
    """
    Exports raw poll votes in valid CSV or JSON format (PRD §4.3).
    """
    poll = await pb.get_poll(poll_id)
    if not poll or poll.get("owner") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized or poll not found.",
        )

    votes = await pb.list_votes_for_poll(poll_id)
    option_map = {opt["id"]: opt.get("text", opt["id"]) for opt in poll.get("options", [])}

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Vote ID", "Option ID", "Option Text", "Created At", "Referrer"])
        for v in votes:
            writer.writerow([
                v.get("id"),
                v.get("option_id"),
                option_map.get(v.get("option_id"), ""),
                v.get("created"),
                v.get("embed_referrer") or "Direct",
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="poll_{poll_id}_votes.csv"'
            },
        )

    # Valid JSON serialization using json.dumps (fixing single-quote bug)
    export_data = [
        {
            "id": v.get("id"),
            "option_id": v.get("option_id"),
            "option_text": option_map.get(v.get("option_id"), ""),
            "created": v.get("created"),
            "referrer": v.get("embed_referrer") or "Direct",
        }
        for v in votes
    ]
    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="poll_{poll_id}_votes.json"'
        },
    )
