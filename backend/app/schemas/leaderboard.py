from pydantic import BaseModel, ConfigDict
from app.schemas.poll import PollResponse

class MostVotedOptionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    poll_id: str
    poll_title: str
    option_id: str
    option_text: str
    vote_count: int

class LeaderboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leaderboard: list[PollResponse]
    total: int

class MostVotedOptionsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[MostVotedOptionItem]
    total: int
