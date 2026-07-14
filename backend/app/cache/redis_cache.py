"""
Thin cache wrapper. Uses Redis when reachable; falls back to a simple
in-process dict with TTL so the API still works locally without a
Redis container running (useful for hackathon demos / CI).
"""
import json
import time
import logging
import redis
from app.config import get_settings

logger = logging.getLogger("alphaflow.cache")
settings = get_settings()

_memory_store: dict[str, tuple[float, str]] = {}


class Cache:
    def __init__(self):
        self._client = None
        try:
            self._client = redis.from_url(settings.redis_url, socket_connect_timeout=1)
            self._client.ping()
        except Exception:
            logger.warning("Redis unavailable, falling back to in-memory cache.")
            self._client = None

    def get(self, key: str):
        if self._client:
            try:
                val = self._client.get(key)
                return json.loads(val) if val else None
            except Exception:
                return None
        entry = _memory_store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            _memory_store.pop(key, None)
            return None
        return json.loads(value)

    def set(self, key: str, value, ttl: int | None = None):
        ttl = ttl or settings.cache_ttl_seconds
        payload = json.dumps(value, default=str)
        if self._client:
            try:
                self._client.setex(key, ttl, payload)
                return
            except Exception:
                pass
        _memory_store[key] = (time.time() + ttl, payload)


_cache_instance: Cache | None = None


def get_cache() -> Cache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache()
    return _cache_instance
