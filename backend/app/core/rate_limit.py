"""IP-hash sliding-window rate limiting for the vote endpoint (PRD §4.6).

Scope: this limiter lives in process memory, so each uvicorn worker keeps its
own window and the effective ceiling is VOTE_RATE_LIMIT_PER_MINUTE multiplied by
the worker count. It is a coarse abuse brake, not a global quota; the durable
one-vote-per-device check is the device token in votes.py. Move this to Redis if
a strict cross-worker limit is ever required.
"""

import hashlib
import time

from app.core.config import settings

# ip_hash -> timestamps of recent requests, pruned as it is read.
_ip_request_history: dict[str, list[float]] = {}

WINDOW_SECONDS = 60.0

# Ceiling on tracked hashes. Without it the dict grows once per distinct client
# for the process lifetime, since entries were never removed.
MAX_TRACKED_IPS = 20_000

_last_sweep = 0.0
SWEEP_INTERVAL_SECONDS = 60.0


def hash_ip(ip_address: str) -> str:
    """Hashes an IP with the configured salt so raw addresses are never stored (PRD §5)."""
    salted = f"{ip_address}:{settings.IP_HASH_SALT}"
    return hashlib.sha256(salted.encode()).hexdigest()


def _sweep(now: float) -> None:
    """Drops hashes with no activity in the current window."""
    global _last_sweep
    cutoff = now - WINDOW_SECONDS
    stale = [key for key, hits in _ip_request_history.items() if not hits or hits[-1] <= cutoff]
    for key in stale:
        del _ip_request_history[key]
    _last_sweep = now

    # Hard cap: if a burst of distinct clients still leaves the map oversized,
    # evict the least recently active entries.
    if len(_ip_request_history) > MAX_TRACKED_IPS:
        ordered = sorted(_ip_request_history.items(), key=lambda kv: kv[1][-1])
        for key, _ in ordered[: len(_ip_request_history) - MAX_TRACKED_IPS]:
            del _ip_request_history[key]


def check_ip_rate_limit(ip_address: str) -> bool:
    """
    Records a request against the IP's window.
    Returns True when allowed, False when throttled.
    """
    ip_h = hash_ip(ip_address)
    now = time.time()

    if now - _last_sweep > SWEEP_INTERVAL_SECONDS:
        _sweep(now)

    window_start = now - WINDOW_SECONDS
    history = [t for t in _ip_request_history.get(ip_h, []) if t > window_start]

    if len(history) >= settings.VOTE_RATE_LIMIT_PER_MINUTE:
        _ip_request_history[ip_h] = history
        return False

    history.append(now)
    _ip_request_history[ip_h] = history
    return True


def reset_rate_limit_state() -> None:
    """Clears all tracked windows. Intended for tests."""
    _ip_request_history.clear()
