from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )

    PROJECT_NAME: str = "Polls Lab API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # PocketBase config parsed directly by pydantic-settings
    POCKETBASE_URL: str = "http://127.0.0.1:8090"
    POCKETBASE_ADMIN_EMAIL: str = ""
    POCKETBASE_ADMIN_PASSWORD: str = ""

    # Platform frontend origins for protected management operations
    FRONTEND_URL: str = "http://localhost:4321"
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:4321",
        "http://127.0.0.1:4321",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Security & Abuse Prevention
    IP_HASH_SALT: str = "change-in-production-salt"
    VOTE_RATE_LIMIT_PER_MINUTE: int = 30

settings = Settings()
