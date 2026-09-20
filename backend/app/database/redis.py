"""
Redis cache abstraction.

Provides a tiny async `Cache` interface used for:
  * analysis result caching        -> key `analysis:{url_hash}`
  * temporary analysis job state   -> key `job:{job_id}`
  * rate limiting                  -> key `ratelimit:{user}:{minute}`

If `REDIS_URL` is unreachable, an in-process `MemoryCache` with TTL support is
used so the application keeps working in demo mode.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Protocol, Tuple

from app.config import get_settings

logger = logging.getLogger(__name__)


def url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().lower().encode()).hexdigest()[:32]


class Cache(Protocol):
    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def ping(self) -> bool: ...
    async def get_json(self, key: str) -> Optional[Any]: ...
    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def incr_with_ttl(self, key: str, ttl: int) -> int: ...
    @property
    def backend(self) -> str: ...


class MemoryCache:
    """In-process TTL cache used when Redis is not available."""

    backend = "memory"

    def __init__(self) -> None:
        self._data: Dict[str, Tuple[float, str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        logger.warning("Using in-memory cache (Redis unavailable).")

    async def close(self) -> None:
        return None

    async def ping(self) -> bool:
        return True

    def _purge(self) -> None:
        now = time.time()
        for k in [k for k, (exp, _) in self._data.items() if exp and exp < now]:
            del self._data[k]

    async def get_json(self, key: str) -> Optional[Any]:
        async with self._lock:
            self._purge()
            item = self._data.get(key)
            return json.loads(item[1]) if item else None

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            self._data[key] = (time.time() + ttl if ttl else 0, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        async with self._lock:
            self._purge()
            exp, raw = self._data.get(key, (time.time() + ttl, "0"))
            value = int(raw) + 1
            self._data[key] = (exp, str(value))
            return value


class RedisCache:
    backend = "redis"

    def __init__(self, url: str) -> None:
        self._url = url
        self._client = None

    async def connect(self) -> None:
        import redis.asyncio as aioredis  # lazy import

        self._client = aioredis.from_url(self._url, decode_responses=True, socket_connect_timeout=3)
        await self._client.ping()
        logger.info("Connected to Redis")

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception:  # pragma: no cover
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self._client.get(key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        await self._client.set(key, json.dumps(value, default=str), ex=ttl)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        value = await self._client.incr(key)
        if value == 1:
            await self._client.expire(key, ttl)
        return int(value)


_cache: Optional[Cache] = None


async def init_cache() -> Cache:
    global _cache
    settings = get_settings()
    if settings.redis_url:
        cache: Cache = RedisCache(settings.redis_url)
        try:
            await cache.connect()
            _cache = cache
            return cache
        except Exception as exc:  # pragma: no cover - network dependent
            logger.error("Redis connection failed (%s). Falling back to in-memory cache.", exc)
    cache = MemoryCache()
    await cache.connect()
    _cache = cache
    return cache


def get_cache() -> Cache:
    if _cache is None:
        raise RuntimeError("Cache not initialised. Call init_cache() on startup.")
    return _cache


async def close_cache() -> None:
    if _cache is not None:
        await _cache.close()
