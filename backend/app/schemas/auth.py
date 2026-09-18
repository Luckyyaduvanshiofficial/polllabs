from pydantic import BaseModel, ConfigDict

class GitHubAuthUrlResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    auth_url: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    provider: str
    deletion_status: str = "active"
    deletion_scheduled_for: str | None = None

class DeletionStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    message: str
    grace_period_ends_at: str | None = None


class PurgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    purged_count: int
    message: str
