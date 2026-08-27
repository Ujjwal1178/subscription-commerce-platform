"""OTP Utilities - Generate, hash, and verify one-time passwords."""

import secrets
import hashlib


def generate_otp(length: int = 6) -> str:
    """Generate cryptographically secure random OTP. Returns string like: '482917'"""
    min_val = 10 ** (length - 1)
    max_val = (10 ** length) - 1
    otp = secrets.randbelow(max_val - min_val + 1) + min_val
    return str(otp)


def hash_otp(otp: str) -> str:
    """Hash OTP using SHA256 for secure storage. Returns 64-char hex string."""
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def verify_otp(input_otp: str, stored_hash: str) -> bool:
    """Verify OTP against stored hash using constant-time comparison."""
    input_hash = hash_otp(input_otp)
    return secrets.compare_digest(input_hash, stored_hash)
