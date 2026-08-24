"""
Redis Client Utility

Provides:
- Connection pool (reuse connections, don't create new every time)
- Singleton pattern (one pool for entire app)
- Health check (is Redis alive?)
- Graceful error handling

Usage:
    from shared.utils.redis_client import get_redis_client
    
    redis = get_redis_client()
    redis.set("key", "value")
    redis.get("key")
"""

import os
import redis
from redis import ConnectionPool, Redis
from typing import Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

# Read from environment (same as docker-compose)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")  # 'redis' is Docker service name
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)  # Optional, we don't use in dev

# Connection Pool Settings
# -------------------------
# max_connections: Maximum connections in pool
#   - Too low = waiting for connections
#   - Too high = Redis overloaded
#   - 10 is good for development, 50-100 for production
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", 10))


# =============================================================================
# SINGLETON CONNECTION POOL
# =============================================================================

# Why Singleton?
# --------------
# Creating connection pool is expensive (network handshake, memory allocation)
# We create ONCE and reuse everywhere.
# 
# Without singleton:
#   get_redis() → new pool → new connections (WRONG!)
#   get_redis() → new pool → new connections (WRONG!)
#
# With singleton:
#   get_redis() → same pool → reused connections (CORRECT!)
#   get_redis() → same pool → reused connections (CORRECT!)

_redis_pool: Optional[ConnectionPool] = None


def _get_connection_pool() -> ConnectionPool:
    """
    Get or create Redis connection pool (Singleton).
    
    Connection Pool Explained:
    --------------------------
    Think of it like a parking lot for connections:
    
    ┌─────────────────────────────────────┐
    │         Connection Pool             │
    │  ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
    │  │Conn│ │Conn│ │Conn│ │Conn│ ...   │
    │  │ 1  │ │ 2  │ │ 3  │ │ 4  │       │
    │  └────┘ └────┘ └────┘ └────┘       │
    └─────────────────────────────────────┘
           ↑         ↑
        Request 1  Request 2
        (uses #1)  (uses #2)
    
    When request finishes, connection returns to pool.
    Next request picks up an available connection.
    
    Returns:
        ConnectionPool: Shared pool instance
    """
    global _redis_pool
    
    if _redis_pool is None:
        # First call - create the pool
        _redis_pool = ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            max_connections=REDIS_MAX_CONNECTIONS,
            # decode_responses=True means Redis returns strings, not bytes
            # Without it: redis.get("key") → b"value" (bytes)
            # With it: redis.get("key") → "value" (string)
            decode_responses=True,
            # Socket timeout - don't wait forever if Redis is slow/down
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    
    return _redis_pool


# =============================================================================
# PUBLIC API
# =============================================================================

def get_redis_client() -> Redis:
    """
    Get Redis client with connection from pool.
    
    This is the main function you'll use everywhere!
    
    Usage:
        redis = get_redis_client()
        
        # String operations
        redis.set("key", "value")
        redis.get("key")
        
        # With expiry (TTL)
        redis.setex("key", 60, "value")  # Expires in 60 seconds
        
        # Increment (atomic!)
        redis.incr("counter")  # Returns new value
        
        # Check if key exists
        redis.exists("key")  # Returns 1 or 0
        
        # Delete key
        redis.delete("key")
    
    Returns:
        Redis: Redis client instance
    """
    pool = _get_connection_pool()
    return Redis(connection_pool=pool)


def check_redis_health() -> bool:
    """
    Check if Redis is alive and responding.
    
    Use this in:
    - Health check endpoints (/health)
    - Startup validation
    - Monitoring
    
    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    try:
        redis = get_redis_client()
        # PING command - Redis responds with PONG
        response = redis.ping()
        return response == True  # ping() returns True on success
    except redis.ConnectionError:
        return False
    except redis.TimeoutError:
        return False
    except Exception:
        return False


def close_redis_pool() -> None:
    """
    Close all connections in the pool.
    
    Call this on app shutdown to cleanup properly.
    
    Usage:
        # In FastAPI
        @app.on_event("shutdown")
        def shutdown():
            close_redis_pool()
    """
    global _redis_pool
    
    if _redis_pool is not None:
        _redis_pool.disconnect()
        _redis_pool = None


# =============================================================================
# CONVENIENCE FUNCTIONS (Optional helpers)
# =============================================================================

def redis_set_with_ttl(key: str, value: str, ttl_seconds: int) -> bool:
    """
    Set a key with automatic expiry.
    
    Args:
        key: Redis key
        value: Value to store
        ttl_seconds: Time to live in seconds
        
    Returns:
        bool: True if successful
        
    Example:
        # Store OTP block status for 20 minutes
        redis_set_with_ttl("blocked:user123", "1", 20 * 60)
    """
    try:
        redis = get_redis_client()
        redis.setex(key, ttl_seconds, value)
        return True
    except Exception:
        return False


def redis_get(key: str) -> Optional[str]:
    """
    Get value by key, returns None if not found.
    
    Args:
        key: Redis key
        
    Returns:
        Value as string, or None if key doesn't exist
    """
    try:
        redis = get_redis_client()
        return redis.get(key)
    except Exception:
        return None


def redis_increment(key: str, ttl_seconds: Optional[int] = None) -> int:
    """
    Atomic increment - perfect for counters and rate limiting!
    
    Why "atomic"?
    -------------
    Normal increment (NOT atomic):
        1. Read value: 5
        2. Add 1: 6
        3. Write back: 6
    
    Problem: If two requests do this simultaneously:
        Request A reads: 5
        Request B reads: 5
        Request A writes: 6
        Request B writes: 6  ← Should be 7!
    
    Atomic increment:
        INCR key → Redis does read+add+write in ONE operation
        No race condition possible!
    
    Args:
        key: Redis key
        ttl_seconds: Optional TTL (set only if key is new)
        
    Returns:
        New value after increment
        
    Example:
        # Rate limiting counter
        count = redis_increment("rate:user123", ttl_seconds=60)
        if count > 10:
            raise TooManyRequestsError()
    """
    try:
        redis = get_redis_client()
        
        # INCR atomically increments (creates key with 0 if doesn't exist)
        count = redis.incr(key)
        
        # Set TTL only on first increment (count == 1)
        # This ensures the window starts from first request
        if ttl_seconds and count == 1:
            redis.expire(key, ttl_seconds)
        
        return count
    except Exception:
        # On Redis failure, return high number to fail-safe (block requests)
        # Alternatively, you could return 0 to fail-open (allow requests)
        return 999999  # Fail-safe: block on Redis error


def redis_delete(key: str) -> bool:
    """
    Delete a key.
    
    Args:
        key: Redis key to delete
        
    Returns:
        bool: True if key was deleted, False if didn't exist
    """
    try:
        redis = get_redis_client()
        return redis.delete(key) > 0
    except Exception:
        return False
