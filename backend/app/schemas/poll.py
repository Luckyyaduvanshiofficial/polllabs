from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

VisibilityType = Literal["public", "private"]
ResultDisplayType = Literal["show_counts", "show_percentage", "hidden_until_close"]

ThemeType = Literal["minimal", "whatsapp", "telegram", "story", "youtube-grid"]
RadiusType = Literal["pill", "rounded", "sharp"]
AppearanceFontType = Literal["system", "serif", "mono", "condensed"]
EffectType = Literal["none", "confetti"]
LayoutType = Literal["list", "grid"]

_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

class PollAppearance(BaseModel):
    """Per-poll visual customization (Phase 7 poll themes). All color fields are optional hex overrides."""

    model_config = ConfigDict(from_attributes=True)
    theme: ThemeType = "minimal"
    bg: str | None = Field(default=None, max_length=7)
    accent: str | None = Field(default=None, max_length=7)
    ink: str | None = Field(default=None, max_length=7)
    radius: RadiusType = "rounded"
    font: AppearanceFontType = "system"
    effect: EffectType = "none"
    layout: LayoutType = "list"

    @field_validator("bg", "accent", "ink")
    @classmethod
    def validate_hex_color(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _HEX_COLOR_RE.match(value):
            raise ValueError("must be a hex color like #fff or #00a884")
        return value.lower()

class PollOptionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str = Field(min_length=1, max_length=200)
    icon_or_image: str | None = None

class PollOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    text: str
    icon_or_image: str | None = None
    vote_count: int | None = None
    percentage: float | None = None
    is_correct: bool | None = None
    voters: list[str] | None = None

class PollCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    options: list[PollOptionCreate | str] = Field(min_length=2, max_length=10)
    visibility: VisibilityType = "public"
    result_display: ResultDisplayType = "show_counts"
    close_at: datetime | str | None = None
    appearance: PollAppearance | None = None
    max_selections: int = Field(default=1, ge=1, le=10)
    is_quiz: bool = False
    correct_options: list[str] | None = None
    show_voters: bool = False

class PollUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    visibility: VisibilityType | None = None
    result_display: ResultDisplayType | None = None
    close_at: datetime | str | None = None
    appearance: PollAppearance | None = None
    max_selections: int | None = Field(default=None, ge=1, le=10)
    is_quiz: bool | None = None
    correct_options: list[str] | None = None
    show_voters: bool | None = None

class PollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str | None = None
    options: list[PollOptionResponse]
    visibility: VisibilityType
    result_display: ResultDisplayType
    owner: str
    total_votes: int | None = None
    created: str
    updated: str
    close_at: datetime | str | None = None
    appearance: PollAppearance | None = None
    max_selections: int = 1
    is_quiz: bool = False
    show_voters: bool = False

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

class PollReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    poll_id: str
    message: str

class PollImageResponse(BaseModel):
    """Phase 4: reference to an uploaded poll option image."""

    model_config = ConfigDict(from_attributes=True)
    id: str
    url: str
