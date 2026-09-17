import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PollLabs API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # PocketBase config (loaded securely from environment or .env)
    POCKETBASE_URL: str = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
    POCKETBASE_ADMIN_EMAIL: str = os.getenv("POCKETBASE_ADMIN_EMAIL", "")
    POCKETBASE_ADMIN_PASSWORD: str = os.getenv("POCKETBASE_ADMIN_PASSWORD", "")

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:4321",
        "http://127.0.0.1:4321",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Security & Abuse Prevention
    IP_HASH_SALT: str = os.getenv("IP_HASH_SALT", "dev-salt-change-in-prod")
    VOTE_RATE_LIMIT_PER_MINUTE: int = 30

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
