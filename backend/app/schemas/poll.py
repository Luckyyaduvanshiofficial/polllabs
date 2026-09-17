from typing import Optional, Literal
from pydantic import BaseModel, Field

VisibilityType = Literal["public", "private"]
ResultDisplayType = Literal["show_counts", "show_percentage", "hidden_until_close"]

class PollOptionBase(BaseModel):
    id: str
    text: str
    icon_or_image: Optional[str] = None
    vote_count: int = 0

class PollCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    options: list[str] = Field(..., min_items=2, max_items=10)
    visibility: VisibilityType = "public"
    result_display: ResultDisplayType = "show_counts"
    close_at: Optional[str] = None

class PollResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    options: list[PollOptionBase]
    visibility: VisibilityType
    result_display: ResultDisplayType
    owner_id: str
    total_votes: int = 0
    created_at: str
    close_at: Optional[str] = None
