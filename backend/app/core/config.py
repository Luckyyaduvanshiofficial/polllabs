import secrets

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_ORIGINS = [
    "http://localhost:4321",
    "http://127.0.0.1:4321",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


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

    # Platform frontend origins for protected management operations.
    # Accepts ALLOWED_ORIGINS as an alias so existing deployments keep working.
    FRONTEND_URL: str = "http://localhost:4321"
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: list(DEV_ORIGINS),
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS", "ALLOWED_ORIGINS"),
    )

    # Security & Abuse Prevention.
    # IP_HASH_SALT has no usable default: an unset salt makes stored ip_hash
    # values brute-forceable across the whole IPv4 space (PRD §5). Accepts
    # SECRET_SALT as an alias so existing deployments keep working.
    IP_HASH_SALT: str = Field(
        default="",
        validation_alias=AliasChoices("IP_HASH_SALT", "SECRET_SALT"),
    )
    VOTE_RATE_LIMIT_PER_MINUTE: int = 30

    # Key for administrative endpoints (account purge). Separate from the
    # PocketBase admin password so the two can be rotated independently.
    ADMIN_API_KEY: str = ""

    # Development-only auth shortcut (x-dev-user-id header). Defaults to off so
    # a deploy that forgets to set ENVIRONMENT still refuses unauthenticated
    # identity claims — fail closed, not open.
    ALLOW_DEV_AUTH_HEADERS: bool = False

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        """Accepts a comma-separated origin list, which is how env vars carry it."""
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return stripped
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() == "production"

    @model_validator(mode="after")
    def enforce_secrets(self) -> "Settings":
        """
        Fails closed on missing secrets rather than falling back to a published
        constant. In production a missing salt or admin key aborts startup; in
        development an ephemeral per-process salt is generated so hashes are
        never computed under a well-known value (PRD §5).
        """
        if self.is_production:
            missing = [
                name
                for name, value in (
                    ("IP_HASH_SALT", self.IP_HASH_SALT),
                    ("ADMIN_API_KEY", self.ADMIN_API_KEY),
                )
                if not value.strip()
            ]
            if missing:
                raise ValueError(
                    "Refusing to start in production without: "
                    + ", ".join(missing)
                    + ". Set them in the environment."
                )
            if self.ALLOW_DEV_AUTH_HEADERS:
                raise ValueError(
                    "ALLOW_DEV_AUTH_HEADERS must be false in production."
                )
        elif not self.IP_HASH_SALT.strip():
            object.__setattr__(self, "IP_HASH_SALT", secrets.token_hex(32))
        return self


settings = Settings()
