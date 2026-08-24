"""
Shared Utilities

Common utility functions used across all services.
"""

from .security import hash_password, verify_password
from .encryption import encrypt_data, decrypt_data, generate_hash, mask_email
from .otp import generate_otp, hash_otp, verify_otp
from .redis_client import (
    get_redis_client,
    check_redis_health,
    close_redis_pool,
    redis_set_with_ttl,
    redis_get,
    redis_increment,
    redis_delete,
)
from .rate_limiter import (
    RateLimiter,
    RateLimitAction,
    RateLimitInfo,
    rate_limiter,
    check_rate_limit,
)

__all__ = [
    # Security (Password)
    "hash_password",
    "verify_password",
    
    # Encryption (AES + SHA256)
    "encrypt_data",
    "decrypt_data", 
    "generate_hash",
    "mask_email",
    
    # OTP
    "generate_otp",
    "hash_otp",
    "verify_otp",
    
    # Redis
    "get_redis_client",
    "check_redis_health",
    "close_redis_pool",
    "redis_set_with_ttl",
    "redis_get",
    "redis_increment",
    "redis_delete",
    
    # Rate Limiter
    "RateLimiter",
    "RateLimitAction",
    "RateLimitInfo",
    "rate_limiter",
    "check_rate_limit",
]
