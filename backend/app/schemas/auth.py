from pydantic import BaseModel, ConfigDict

class GitHubAuthUrlResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    auth_url: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    provider: str

class DeletionStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    message: str
    grace_period_ends_at: str | None = None
