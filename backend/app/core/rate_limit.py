"""Lightweight in-process fixed-window rate limiting for auth endpoints.

This is intentionally simple (single-instance) and is documented as such. The
existing Redis-backed middleware handles general API throttling; this dependency
adds brute-force/OTP-spam protection on sensitive endpoints.
"""

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.core.config import settings

_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
_hits: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request, scope: str) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else ""
    ip = ip or (request.client.host if request.client else "unknown")
    return f"{scope}:{ip}"


def rate_limit(scope: str, limit: int, window_seconds: int = 60):
    """Return a FastAPI dependency that enforces `limit` requests per window."""

    def _dep(request: Request) -> None:
        key = _client_key(request, scope)
        now = time.time()
        cutoff = now - window_seconds
        with _locks[key]:
            recent = [t for t in _hits[key] if t > cutoff]
            if len(recent) >= limit:
                retry = int(window_seconds - (now - recent[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Try again in {retry} seconds.",
                    headers={"Retry-After": str(retry)},
                )
            recent.append(now)
            _hits[key] = recent

    return _dep


# Preconfigured limiters used by the routes (configurable via environment).
auth_limiter = rate_limit("auth", settings.RATE_LIMIT_AUTH_PER_MINUTE)
otp_limiter = rate_limit("otp", settings.RATE_LIMIT_OTP_PER_MINUTE)
