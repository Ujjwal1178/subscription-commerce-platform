"""
OTP (One-Time Password) Utilities

Functions:
- generate_otp(): Create random 6-digit OTP
- hash_otp(): Hash OTP for secure storage
- verify_otp(): Compare input OTP with stored hash

Why hash OTP?
- Even 6-digit OTP should not be stored in plain text
- If DB leaks, attacker can't use OTPs directly
- Same principle as passwords, just simpler
"""

import secrets
import hashlib


# =============================================================================
# OTP GENERATION
# =============================================================================

def generate_otp(length: int = 6) -> str:
    """
    Generate a cryptographically secure random OTP.
    
    Args:
        length: Number of digits (default: 6)
        
    Returns:
        String of random digits (e.g., "482917")
        
    Example:
        >>> otp = generate_otp()
        >>> print(otp)
        '482917'
        >>> len(otp)
        6
        
    Why secrets module?
        - random.randint() is NOT cryptographically secure
        - secrets module uses OS-level randomness
        - Safe for security-sensitive applications
    """
    # Generate random number with exact digits
    # For 6 digits: range is 100000 to 999999
    min_val = 10 ** (length - 1)      # 100000
    max_val = (10 ** length) - 1       # 999999
    
    otp = secrets.randbelow(max_val - min_val + 1) + min_val
    return str(otp)


# =============================================================================
# OTP HASHING (for secure storage)
# =============================================================================

def hash_otp(otp: str) -> str:
    """
    Hash OTP using SHA256 for secure storage.
    
    Args:
        otp: Plain text OTP (e.g., "482917")
        
    Returns:
        SHA256 hash of OTP (64 characters)
        
    Example:
        >>> hashed = hash_otp("482917")
        >>> print(hashed)
        'a1b2c3d4e5f6...'  # 64 char hex string
        
    Why hash OTP?
        - Never store sensitive data in plain text
        - If DB leaks, hashed OTPs are useless to attacker
        - Same input always gives same hash (for verification)
    """
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def verify_otp(input_otp: str, stored_hash: str) -> bool:
    """
    Verify OTP against stored hash.
    
    Args:
        input_otp: OTP entered by user
        stored_hash: Hashed OTP from database
        
    Returns:
        True if OTP matches, False otherwise
        
    Example:
        >>> otp = generate_otp()  # "482917"
        >>> stored = hash_otp(otp)  # Store this in DB
        >>> 
        >>> verify_otp("482917", stored)  # User enters correct OTP
        True
        >>> verify_otp("000000", stored)  # User enters wrong OTP
        False
    """
    input_hash = hash_otp(input_otp)
    return secrets.compare_digest(input_hash, stored_hash)
