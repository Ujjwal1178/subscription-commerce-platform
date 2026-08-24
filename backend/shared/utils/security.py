"""
Password Security Utilities

Uses bcrypt for password hashing.
bcrypt is intentionally slow to prevent brute-force attacks.
"""

import bcrypt


# Cost factor (rounds) - 2^12 = 4096 iterations
# Increase this as hardware gets faster (every 2-3 years)
BCRYPT_ROUNDS = 12


def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        plain_password: The plain text password from user
        
    Returns:
        Hashed password string to store in database
        
    Example:
        >>> hashed = hash_password("Secret@123")
        >>> print(hashed)
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCO...'
        
    How bcrypt works:
        1. Generates random 22-character salt
        2. Combines password + salt
        3. Runs 2^BCRYPT_ROUNDS iterations of hashing
        4. Returns: $2b$12$<salt><hash>
    """
    # Generate salt with specified rounds (cost factor)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    
    # Hash password (must encode to bytes)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    
    # Return as string (for DB storage)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against stored hash.
    
    Args:
        plain_password: Password entered by user during login
        hashed_password: Stored hash from database
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("Secret@123")
        >>> verify_password("Secret@123", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
        
    How verification works:
        1. bcrypt extracts salt from stored hash
        2. Hashes input password with same salt
        3. Compares result with stored hash
        4. Returns True/False
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
