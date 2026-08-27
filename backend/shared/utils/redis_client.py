"""Redis Client - Connection pool with singleton pattern."""

import os
import redis
from redis import ConnectionPool, Redis
from typing import Optional

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", 10))

_redis_pool: Optional[ConnectionPool] = None


def _get_connection_pool() -> ConnectionPool:
    """Get or create Redis connection pool (singleton)."""
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            max_connections=REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    
    return _redis_pool


def get_redis_client() -> Redis:
    """Get Redis client with connection from pool."""
    return Redis(connection_pool=_get_connection_pool())


def check_redis_health() -> bool:
    """Check if Redis is alive. Returns True if healthy."""
    try:
        return get_redis_client().ping() == True
    except Exception:
        return False


def close_redis_pool() -> None:
    """Close all connections in pool. Call on app shutdown."""
    global _redis_pool
    if _redis_pool is not None:
        _redis_pool.disconnect()
        _redis_pool = None


def redis_set_with_ttl(key: str, value: str, ttl_seconds: int) -> bool:
    """Set key with automatic expiry."""
    try:
        get_redis_client().setex(key, ttl_seconds, value)
        return True
    except Exception:
        return False


def redis_get(key: str) -> Optional[str]:
    """Get value by key, returns None if not found."""
    try:
        return get_redis_client().get(key)
    except Exception:
        return None


def redis_increment(key: str, ttl_seconds: Optional[int] = None) -> int:
    """Atomic increment - perfect for counters. Sets TTL on first increment."""
    try:
        redis = get_redis_client()
        count = redis.incr(key)
        if ttl_seconds and count == 1:
            redis.expire(key, ttl_seconds)
        return count
    except Exception:
        return 999999  # Fail-safe: high number blocks requests


def redis_delete(key: str) -> bool:
    """Delete a key. Returns True if deleted."""
    try:
        return get_redis_client().delete(key) > 0
    except Exception:
        return False
