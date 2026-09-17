from pydantic import BaseModel, ConfigDict

class VoteRequest(BaseModel):
    option_id: str
    device_token: str | None = None
    embed_referrer: str | None = None

class VoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool
    message: str
    poll_id: str
    device_token: str
