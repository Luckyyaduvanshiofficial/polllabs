from datetime import datetime, timezone

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
