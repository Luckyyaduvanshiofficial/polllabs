from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.poll import PollOptionResponse


class VoteRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    option_id: str | list[str]
    device_token: str | None = None
    embed_referrer: str | None = None

    @field_validator("option_id")
    @classmethod
    def validate_option_id(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, list):
            if len(value) == 0:
                raise ValueError("option_id list must not be empty")
            if len(set(value)) != len(value):
                raise ValueError("option_id list must contain unique values")
        return value


class VoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool
    message: str
    poll_id: str
    device_token: str
    total_votes: int | None = None
    options: list[PollOptionResponse]
    selected_options: list[str] | None = None
