from typing import Literal, Union
from pydantic import BaseModel, Field, ConfigDict

VisibilityType = Literal["public", "private"]
ResultDisplayType = Literal["show_counts", "show_percentage", "hidden_until_close"]

class PollOptionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str = Field(min_length=1, max_length=200)
    icon_or_image: str | None = None

class PollOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    text: str
    icon_or_image: str | None = None
    vote_count: int = 0
    percentage: float | None = None

class PollCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    options: list[Union[PollOptionCreate, str]] = Field(min_length=2, max_length=10)
    visibility: VisibilityType = "public"
    result_display: ResultDisplayType = "show_counts"
    close_at: str | None = None

class PollUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    visibility: VisibilityType | None = None
    result_display: ResultDisplayType | None = None
    close_at: str | None = None

class PollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str | None = None
    options: list[PollOptionResponse]
    visibility: VisibilityType
    result_display: ResultDisplayType
    owner: str
    total_votes: int = 0
    created: str
    updated: str
    close_at: str | None = None

class PollListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[PollResponse]
    page: int
    per_page: int
    total_items: int
    total_pages: int

class PollReportRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reason: str = Field(min_length=5, max_length=500)
