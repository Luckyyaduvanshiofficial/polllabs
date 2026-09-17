from pydantic import BaseModel, ConfigDict

class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    poll_id: str
    title: str
    total_votes: int
    options_breakdown: dict[str, int]
    referrers_breakdown: dict[str, int]
    votes_over_time: dict[str, int]  # Date formatted timeline (e.g. YYYY-MM-DD: count)
