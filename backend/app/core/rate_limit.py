import hashlib
import time
from collections import defaultdict
from app.core.config import settings

# Memory-based sliding window rate limiter for development
# Key: ip_hash, Value: list of request timestamps
_ip_request_history: dict[str, list[float]] = defaultdict(list)

def hash_ip(ip_address: str) -> str:
    """Hashes IP address with salt to comply with privacy requirement (§5)."""
    salted = f"{ip_address}:{settings.IP_HASH_SALT}"
    return hashlib.sha256(salted.encode()).hexdigest()

def check_ip_rate_limit(ip_address: str) -> bool:
    """
    Checks if an IP hash exceeded the votes/minute limit.
    Returns True if allowed, False if throttled.
    """
    ip_h = hash_ip(ip_address)
    now = time.time()
    one_minute_ago = now - 60.0

    # Clean old records
    history = [t for t in _ip_request_history[ip_h] if t > one_minute_ago]
    if len(history) >= settings.VOTE_RATE_LIMIT_PER_MINUTE:
        _ip_request_history[ip_h] = history
        return False

    history.append(now)
    _ip_request_history[ip_h] = history
    return True
