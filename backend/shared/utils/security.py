"""Password Security - bcrypt hashing (intentionally slow for brute-force protection)."""

import bcrypt

BCRYPT_ROUNDS = 12  # 2^12 = 4096 iterations


def hash_password(plain_password: str) -> str:
    """Hash password using bcrypt. Returns string like: $2b$12$<salt><hash>"""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash. Returns True if match."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
