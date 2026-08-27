"""Rate Limiter - Redis-based fixed window rate limiting."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from .redis_client import get_redis_client
from .encryption import generate_hash


class RateLimitAction(str, Enum):
    """Predefined rate limit actions."""
    LOGIN = "login"
    REGISTER = "register"
    OTP_VERIFY = "otp_verify"
    OTP_RESEND = "otp_resend"
    PASSWORD_RESET = "password_reset"
    REFRESH_TOKEN = "refresh_token"


@dataclass
class RateLimitInfo:
    """Rate limit status response."""
    allowed: bool
    current_count: int
    limit: int
    remaining: int
    retry_after: Optional[int]
    window_seconds: int


class RateLimiter:
    """Redis-based rate limiter using fixed window algorithm."""
    
    def __init__(self, key_prefix: str = "rate"):
        self.key_prefix = key_prefix
    
    def _generate_key(self, action: str, identifier: str) -> str:
        """Generate Redis key: {prefix}:{action}:{identifier_hash}"""
        identifier_hash = generate_hash(identifier.lower())[:16]
        return f"{self.key_prefix}:{action}:{identifier_hash}"
    
    def check_rate_limit(self, action: str, identifier: str, limit: int, window_seconds: int = 60) -> RateLimitInfo:
        """Check if request is allowed. Returns RateLimitInfo with status."""
        key = self._generate_key(action, identifier)
        
        try:
            redis = get_redis_client()
            current_count = redis.incr(key)
            
            if current_count == 1:
                redis.expire(key, window_seconds)
            
            ttl = redis.ttl(key)
            if ttl < 0:
                ttl = window_seconds
            
            remaining = max(0, limit - current_count)
            allowed = current_count <= limit
            
            return RateLimitInfo(
                allowed=allowed,
                current_count=current_count,
                limit=limit,
                remaining=remaining,
                retry_after=ttl if not allowed else None,
                window_seconds=window_seconds
            )
        except Exception as e:
            import logging
            logging.error(f"Rate limiter Redis error: {e}")
            # Fail-open: allow request if Redis is down
            return RateLimitInfo(allowed=True, current_count=0, limit=limit, remaining=limit, retry_after=None, window_seconds=window_seconds)
    
    def reset_limit(self, action: str, identifier: str) -> bool:
        """Reset rate limit for action/identifier."""
        try:
            get_redis_client().delete(self._generate_key(action, identifier))
            return True
        except Exception:
            return False
    
    def get_status(self, action: str, identifier: str, limit: int, window_seconds: int = 60) -> RateLimitInfo:
        """Get current status WITHOUT incrementing."""
        key = self._generate_key(action, identifier)
        
        try:
            redis = get_redis_client()
            count_str = redis.get(key)
            current_count = int(count_str) if count_str else 0
            ttl = redis.ttl(key)
            if ttl < 0:
                ttl = window_seconds
            
            remaining = max(0, limit - current_count)
            allowed = current_count < limit
            
            return RateLimitInfo(allowed=allowed, current_count=current_count, limit=limit, remaining=remaining, retry_after=ttl if not allowed else None, window_seconds=window_seconds)
        except Exception:
            return RateLimitInfo(allowed=True, current_count=0, limit=limit, remaining=limit, retry_after=None, window_seconds=window_seconds)


# Singleton instance
rate_limiter = RateLimiter()


def check_rate_limit(action: str, identifier: str, limit: int, window_seconds: int = 60) -> RateLimitInfo:
    """Convenience function using default rate limiter."""
    return rate_limiter.check_rate_limit(action, identifier, limit, window_seconds)
