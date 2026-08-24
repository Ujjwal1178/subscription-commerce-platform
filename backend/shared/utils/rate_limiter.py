"""
Rate Limiter Utility

Provides Redis-based rate limiting for protecting APIs from abuse.

How Rate Limiting Works:
------------------------
Imagine a bucket that fills with water (requests).
- Water drips in = requests coming in
- Bucket has max capacity = rate limit
- Bucket empties over time = TTL window resets

If bucket is full, reject the request!

Implementation:
---------------
We use "Fixed Window" algorithm:
- Window = time period (e.g., 60 seconds)
- Count requests in current window
- If count > limit, reject

Key Format:
-----------
rate:{action}:{identifier_hash}

Examples:
- rate:login:dd929a27a10d8a0...      (login attempts by email hash)
- rate:otp_verify:dd929a27a10d8a0... (OTP verify attempts by email hash)
- rate:otp_resend:dd929a27a10d8a0... (OTP resend attempts by email hash)

Usage:
    from shared.utils.rate_limiter import RateLimiter
    
    limiter = RateLimiter()
    
    # Check rate limit
    allowed, info = limiter.check_rate_limit(
        action="otp_verify",
        identifier="ujjwal@gmail.com",
        limit=5,
        window_seconds=60
    )
    
    if not allowed:
        raise HTTPException(429, f"Too many requests. Retry after {info['retry_after']} seconds")
"""

import time
from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum

from .redis_client import get_redis_client, redis_increment
from .encryption import generate_hash


# =============================================================================
# RATE LIMIT ACTIONS (Enum for type safety)
# =============================================================================

class RateLimitAction(str, Enum):
    """
    Predefined rate limit actions.
    
    Using Enum instead of plain strings:
    - Prevents typos ("logiin" vs "login")
    - IDE autocomplete works
    - Easy to see all actions in one place
    """
    LOGIN = "login"
    REGISTER = "register"
    OTP_VERIFY = "otp_verify"
    OTP_RESEND = "otp_resend"
    PASSWORD_RESET = "password_reset"
    REFRESH_TOKEN = "refresh_token"


# =============================================================================
# RATE LIMIT INFO (Response Data)
# =============================================================================

@dataclass
class RateLimitInfo:
    """
    Information about rate limit status.
    
    Attributes:
        allowed: Whether request is allowed
        current_count: How many requests made in current window
        limit: Maximum allowed requests
        remaining: How many requests left
        retry_after: Seconds until rate limit resets (only if blocked)
        window_seconds: Length of the time window
    """
    allowed: bool
    current_count: int
    limit: int
    remaining: int
    retry_after: Optional[int]  # Seconds until reset
    window_seconds: int


# =============================================================================
# RATE LIMITER CLASS
# =============================================================================

class RateLimiter:
    """
    Redis-based rate limiter.
    
    Why a class?
    ------------
    - Can be configured (default limits, key prefix)
    - Easier to mock in tests
    - Can add methods like reset_limit(), get_status()
    
    Usage:
        limiter = RateLimiter()
        
        result = limiter.check_rate_limit(
            action=RateLimitAction.OTP_VERIFY,
            identifier="ujjwal@gmail.com",
            limit=5,
            window_seconds=60
        )
        
        if not result.allowed:
            raise TooManyRequestsError(retry_after=result.retry_after)
    """
    
    def __init__(self, key_prefix: str = "rate"):
        """
        Initialize rate limiter.
        
        Args:
            key_prefix: Prefix for all rate limit keys (default: "rate")
        """
        self.key_prefix = key_prefix
    
    def _generate_key(self, action: str, identifier: str) -> str:
        """
        Generate Redis key for rate limiting.
        
        Key format: {prefix}:{action}:{identifier_hash}
        
        Why hash the identifier?
        ------------------------
        - identifier might be email (PII)
        - We don't want PII in Redis keys
        - Hash is one-way, can't reverse to get email
        
        Args:
            action: The action being rate limited (login, otp_verify, etc.)
            identifier: User identifier (email, user_id, IP, etc.)
            
        Returns:
            Redis key string
        """
        # Hash the identifier to avoid storing PII in Redis
        # Use first 16 chars of hash (enough for uniqueness, shorter keys)
        identifier_hash = generate_hash(identifier.lower())[:16]
        
        return f"{self.key_prefix}:{action}:{identifier_hash}"
    
    def check_rate_limit(
        self,
        action: str,
        identifier: str,
        limit: int,
        window_seconds: int = 60
    ) -> RateLimitInfo:
        """
        Check if request is allowed under rate limit.
        
        Algorithm (Fixed Window):
        -------------------------
        1. Generate key: rate:action:identifier_hash
        2. Increment counter (atomic, creates if not exists)
        3. If first request (count=1), set TTL
        4. Compare count with limit
        
        Args:
            action: What action is being rate limited (login, otp_verify, etc.)
            identifier: Who is making the request (email, user_id, IP)
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds (default: 60)
            
        Returns:
            RateLimitInfo with status and metadata
            
        Example:
            # Allow 5 OTP verify attempts per minute
            result = limiter.check_rate_limit(
                action="otp_verify",
                identifier="user@example.com",
                limit=5,
                window_seconds=60
            )
        """
        key = self._generate_key(action, identifier)
        
        try:
            redis = get_redis_client()
            
            # Atomic increment
            # - If key doesn't exist, creates with value 1
            # - If key exists, increments by 1
            # - Returns new value
            current_count = redis.incr(key)
            
            # Set TTL only on first request (when count becomes 1)
            # This ensures window starts from first request, not randomly
            if current_count == 1:
                redis.expire(key, window_seconds)
            
            # Get remaining TTL (how long until window resets)
            ttl = redis.ttl(key)
            if ttl < 0:  # Key exists but no TTL (shouldn't happen, but safety)
                ttl = window_seconds
            
            # Calculate remaining requests
            remaining = max(0, limit - current_count)
            
            # Is request allowed?
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
            # On Redis failure, we have two options:
            # 1. Fail-open: Allow request (risky, but better UX)
            # 2. Fail-closed: Block request (safer, but bad UX)
            #
            # For security-sensitive actions (login, OTP), we fail-closed
            # For general actions, we could fail-open
            #
            # Here we fail-open to not break the app if Redis is down
            # But log the error for monitoring!
            import logging
            logging.error(f"Rate limiter Redis error: {e}")
            
            # Fail-open: Allow the request
            return RateLimitInfo(
                allowed=True,
                current_count=0,
                limit=limit,
                remaining=limit,
                retry_after=None,
                window_seconds=window_seconds
            )
    
    def reset_limit(self, action: str, identifier: str) -> bool:
        """
        Reset rate limit for a specific action/identifier.
        
        Use cases:
        - User successfully logged in, reset login attempts
        - Admin manually resets a user's limit
        - Testing
        
        Args:
            action: The action to reset
            identifier: The identifier to reset
            
        Returns:
            True if reset successful, False otherwise
        """
        key = self._generate_key(action, identifier)
        
        try:
            redis = get_redis_client()
            redis.delete(key)
            return True
        except Exception:
            return False
    
    def get_status(self, action: str, identifier: str, limit: int, window_seconds: int = 60) -> RateLimitInfo:
        """
        Get current rate limit status WITHOUT incrementing.
        
        Useful for:
        - Showing user how many attempts remaining
        - Admin dashboards
        - Debugging
        
        Args:
            action: The action to check
            identifier: The identifier to check
            limit: The limit for this action
            window_seconds: The window size
            
        Returns:
            RateLimitInfo with current status
        """
        key = self._generate_key(action, identifier)
        
        try:
            redis = get_redis_client()
            
            # GET doesn't increment, just reads
            count_str = redis.get(key)
            current_count = int(count_str) if count_str else 0
            
            ttl = redis.ttl(key)
            if ttl < 0:
                ttl = window_seconds
            
            remaining = max(0, limit - current_count)
            allowed = current_count < limit  # Note: < not <= (next request would exceed)
            
            return RateLimitInfo(
                allowed=allowed,
                current_count=current_count,
                limit=limit,
                remaining=remaining,
                retry_after=ttl if not allowed else None,
                window_seconds=window_seconds
            )
            
        except Exception:
            return RateLimitInfo(
                allowed=True,
                current_count=0,
                limit=limit,
                remaining=limit,
                retry_after=None,
                window_seconds=window_seconds
            )


# =============================================================================
# SINGLETON INSTANCE (Convenience)
# =============================================================================

# Create a default rate limiter instance
# Most code can just use: from shared.utils.rate_limiter import rate_limiter
rate_limiter = RateLimiter()


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def check_rate_limit(
    action: str,
    identifier: str,
    limit: int,
    window_seconds: int = 60
) -> RateLimitInfo:
    """
    Convenience function using default rate limiter.
    
    Usage:
        from shared.utils.rate_limiter import check_rate_limit
        
        result = check_rate_limit("otp_verify", "user@email.com", limit=5)
        if not result.allowed:
            raise HTTPException(429, "Too many requests")
    """
    return rate_limiter.check_rate_limit(action, identifier, limit, window_seconds)
