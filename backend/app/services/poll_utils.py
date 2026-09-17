from datetime import datetime, timezone
from typing import Any

def is_poll_closed(close_at: datetime | str | None) -> bool:
    """
    Determines whether a poll has passed its scheduled close time.
    Handles ISO string timestamps and datetime instances cleanly.
    """
    if not close_at:
        return False

    try:
        if isinstance(close_at, datetime):
            close_time = close_at if close_at.tzinfo else close_at.replace(tzinfo=timezone.utc)
        else:
            cleaned = str(close_at).replace("Z", "+00:00")
            close_time = datetime.fromisoformat(cleaned)
            if not close_time.tzinfo:
                close_time = close_time.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) >= close_time
    except Exception:
        return False

def coerce_appearance(raw: Any) -> Any | None:
    """
    Safely parses the stored `appearance` JSON field into a PollAppearance.
    Returns None for polls created before Phase 7 (missing field) or for
    malformed payloads — the widget falls back to the minimal theme.
    Import is local to avoid a services->schemas hard dependency at module load.
    """
    if not raw or not isinstance(raw, dict):
        return None
    try:
        from app.schemas.poll import PollAppearance

        return PollAppearance.model_validate(raw)
    except Exception:
        return None
