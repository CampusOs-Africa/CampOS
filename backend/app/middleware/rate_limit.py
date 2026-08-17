import logging
import time
import uuid
from collections import defaultdict
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("campusos.ratelimit")

# Atomic Sliding Window Rate Limiting Lua Script for Redis
LUA_SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local max_limit = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
local current_count = redis.call('ZCARD', key)
if current_count >= max_limit then
    return 0
end
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, 60)
return 1
"""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production Hardened Distributed Rate Limiting Middleware.
    - Uses Redis atomic sliding window Lua script when available.
    - Automatically provides graceful fallback to in-memory sliding window when Redis is offline.
    - Enforces configurable limits:
      * Standard endpoints: 100 requests / minute (RATE_LIMIT_DEFAULT_PER_MINUTE)
      * Sensitive endpoints (/upload, /scan, /webhook, /send-email-otp, /verify-email-otp): 30 requests / minute (RATE_LIMIT_SENSITIVE_PER_MINUTE)
    """

    def __init__(self, app, max_requests_per_minute: int = 100):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.ip_records: dict[str, list[float]] = defaultdict(list)
        self._redis_client: Any = None
        self._lua_script: Any = None
        self._redis_available = False
        self._init_redis()

    def _init_redis(self):
        try:
            import redis

            self._redis_client = redis.Redis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_timeout=0.5
            )
            self._lua_script = self._redis_client.register_script(
                LUA_SLIDING_WINDOW_SCRIPT
            )
            self._redis_available = True
            logger.info("Redis distributed rate limiter initialized successfully.")
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Redis rate limiter initialization failed ({e}); falling back to in-memory sliding window."
            )
            self._redis_available = False

    def _is_sensitive_path(self, path: str) -> bool:
        sensitive_keywords = (
            "/upload",
            "/scan",
            "/webhook",
            "/send-email-otp",
            "/verify-email-otp",
        )
        return any(kw in path for kw in sensitive_keywords)

    def _allow_redis_request(self, client_ip: str, max_limit: int, now: float) -> bool:
        try:
            key = f"campusos:ratelimit:{client_ip}"
            window_start = now - 60.0
            member = f"{now}-{uuid.uuid4().hex[:8]}"
            res = self._lua_script(
                keys=[key], args=[now, window_start, max_limit, member]
            )
            return int(res) == 1
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Redis atomic rate limit call failed ({e}); falling back to in-memory sliding window."
            )
            self._redis_available = False
            return self._allow_in_memory_request(client_ip, max_limit, now)

    def _allow_in_memory_request(
        self, client_ip: str, max_limit: int, now: float
    ) -> bool:
        window_start = now - 60.0
        self.ip_records[client_ip] = [
            t for t in self.ip_records[client_ip] if t > window_start
        ]
        if len(self.ip_records[client_ip]) >= max_limit:
            return False
        self.ip_records[client_ip].append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        # Allow test suite requests unless explicitly marked for rate-limit testing
        if (
            settings.ENVIRONMENT == "test"
            and request.headers.get("X-Test-Rate-Limit") != "true"
        ):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        max_limit = (
            settings.RATE_LIMIT_SENSITIVE_PER_MINUTE
            if self._is_sensitive_path(request.url.path)
            else settings.RATE_LIMIT_DEFAULT_PER_MINUTE
        )

        allowed = (
            self._allow_redis_request(client_ip, max_limit, now)
            if (self._redis_available and settings.USE_REDIS_RATE_LIMIT)
            else self._allow_in_memory_request(client_ip, max_limit, now)
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests from IP '{client_ip}'. Please slow down and try again later.",
                    },
                },
                headers={"Retry-After": "60"},
            )

        return await call_next(request)
