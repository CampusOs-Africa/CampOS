import json
import logging
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger("campusos.cache")

_in_memory_cache: dict[str, tuple[str, float]] = {}


def _get_redis_client() -> Any | None:
    try:
        import redis

        return redis.Redis.from_url(
            settings.REDIS_URL, decode_responses=True, socket_timeout=0.3
        )
    except Exception:  # noqa: BLE001
        return None


def cache_get(key: str) -> Any | None:
    """Retrieve JSON-decoded item from Redis or in-memory LRU cache."""
    now = time.time()
    if settings.USE_REDIS_RATE_LIMIT:
        client = _get_redis_client()
        if client:
            try:
                data_str = client.get(key)
                if data_str:
                    return json.loads(data_str)
                return None
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Redis cache read failed ({e}), using in-memory cache")

    # In-memory fallback
    cached = _in_memory_cache.get(key)
    if cached:
        data_str, exp_time = cached
        if now < exp_time:
            try:
                return json.loads(data_str)
            except Exception:  # noqa: BLE001
                return None
        _in_memory_cache.pop(key, None)
    return None


def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    """Store JSON-serializable item in Redis or in-memory LRU cache with TTL."""
    try:
        data_str = json.dumps(value)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to serialize value for cache key {key}: {e}")
        return

    now = time.time()
    if settings.USE_REDIS_RATE_LIMIT:
        client = _get_redis_client()
        if client:
            try:
                client.set(key, data_str, ex=ttl_seconds)
                return
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Redis cache write failed ({e}), using in-memory cache")

    _in_memory_cache[key] = (data_str, now + ttl_seconds)


def cache_delete_pattern(pattern: str) -> None:
    """Delete all cache keys matching a prefix pattern (e.g. campusos:cache:marketplace:*)."""
    if settings.USE_REDIS_RATE_LIMIT:
        client = _get_redis_client()
        if client:
            try:
                keys = client.keys(pattern)
                if keys:
                    client.delete(*keys)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Redis pattern delete failed ({e})")

    # In-memory prefix matching
    prefix = pattern.replace("*", "")
    matching = [k for k in _in_memory_cache if k.startswith(prefix)]
    for k in matching:
        _in_memory_cache.pop(k, None)


def invalidate_marketplace_cache() -> None:
    """Invalidate all cached marketplace categories and catalog queries."""
    cache_delete_pattern("campusos:cache:marketplace:*")
    logger.info("Marketplace catalog cache invalidated.")
