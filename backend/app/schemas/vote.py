from typing import Optional
from pydantic import BaseModel

class VoteRequest(BaseModel):
    option_id: str
    device_token: Optional[str] = None
    embed_referrer: Optional[str] = None

class VoteResponse(BaseModel):
    success: bool
    message: str
    poll_id: str
    device_token: str
