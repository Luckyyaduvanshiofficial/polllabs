from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

VisibilityType = Literal["public", "private"]
ResultDisplayType = Literal["show_counts", "show_percentage", "hidden_until_close"]

class PollOptionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    text: str
    icon_or_image: str | None = None
    vote_count: int = 0

class PollCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    options: list[str] = Field(min_length=2, max_length=10)
    visibility: VisibilityType = "public"
    result_display: ResultDisplayType = "show_counts"
    close_at: str | None = None

class PollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    description: str | None = None
    options: list[PollOptionBase]
    visibility: VisibilityType
    result_display: ResultDisplayType
    owner_id: str
    total_votes: int = 0
    created_at: str
    close_at: str | None = None
