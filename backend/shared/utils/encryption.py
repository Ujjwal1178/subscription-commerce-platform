"""
Encryption Utilities

Two functions:
1. AES-256 Encryption/Decryption - For storing PII (email, phone)
2. SHA256 Hashing - For indexed lookups

AES = Advanced Encryption Standard (symmetric encryption)
- Same key for encrypt and decrypt
- We use AES-256-CBC mode
- IV (Initialization Vector) ensures same input → different output each time
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


# =============================================================================
# CONFIGURATION
# =============================================================================

# AES-256 requires 32-byte key (256 bits)
# In production, this comes from environment variable or secrets manager
# NEVER hardcode in real apps!

def _get_encryption_key() -> bytes:
    """
    Get encryption key from environment.
    
    Key must be exactly 32 bytes for AES-256.
    """
    key = os.environ.get('ENCRYPTION_KEY')
    
    if not key:
        # For development only - use a default key
        # In production, this should raise an error!
        key = 'dev-key-32-bytes-long-exactly!!'  # Exactly 32 chars
    
    key_bytes = key.encode('utf-8')
    
    if len(key_bytes) != 32:
        raise ValueError(f"ENCRYPTION_KEY must be exactly 32 bytes, got {len(key_bytes)}")
    
    return key_bytes


# =============================================================================
# AES ENCRYPTION / DECRYPTION
# =============================================================================

def encrypt_data(plaintext: str) -> str:
    """
    Encrypt data using AES-256-CBC.
    
    Args:
        plaintext: Data to encrypt (e.g., email, phone)
        
    Returns:
        Base64 encoded string: IV + Ciphertext
        
    Example:
        >>> encrypted = encrypt_data("ujjwal@gmail.com")
        >>> print(encrypted)
        'YWJjZGVmZ2hpamtsbW5vcA==...'  # Base64 encoded
        
    How it works:
        1. Generate random 16-byte IV
        2. Pad plaintext to block size (16 bytes)
        3. Encrypt with AES-256-CBC
        4. Combine IV + Ciphertext
        5. Base64 encode for storage
    """
    key = _get_encryption_key()
    
    # Generate random IV (16 bytes for AES)
    iv = os.urandom(16)
    
    # Create cipher
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # Pad plaintext to 16-byte blocks (AES requirement)
    padder = padding.PKCS7(128).padder()  # 128 bits = 16 bytes
    padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
    
    # Encrypt
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Combine IV + Ciphertext and Base64 encode
    combined = iv + ciphertext
    return base64.b64encode(combined).decode('utf-8')


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt AES-256-CBC encrypted data.
    
    Args:
        encrypted_data: Base64 encoded IV + Ciphertext
        
    Returns:
        Original plaintext
        
    Example:
        >>> encrypted = encrypt_data("ujjwal@gmail.com")
        >>> decrypted = decrypt_data(encrypted)
        >>> print(decrypted)
        'ujjwal@gmail.com'
        
    How it works:
        1. Base64 decode
        2. Extract IV (first 16 bytes)
        3. Extract Ciphertext (rest)
        4. Decrypt with same key + IV
        5. Remove padding
    """
    key = _get_encryption_key()
    
    # Base64 decode
    combined = base64.b64decode(encrypted_data.encode('utf-8'))
    
    # Extract IV (first 16 bytes) and ciphertext (rest)
    iv = combined[:16]
    ciphertext = combined[16:]
    
    # Create cipher with same key and extracted IV
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    # Decrypt
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove padding
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_data) + unpadder.finalize()
    
    return plaintext.decode('utf-8')


# =============================================================================
# SHA256 HASHING (for lookups)
# =============================================================================

def generate_hash(data: str) -> str:
    """
    Generate SHA256 hash of data.
    
    Args:
        data: String to hash (e.g., email for lookup)
        
    Returns:
        64-character hex string (256 bits)
        
    Example:
        >>> hash1 = generate_hash("ujjwal@gmail.com")
        >>> hash2 = generate_hash("ujjwal@gmail.com")
        >>> hash1 == hash2
        True  # Same input always gives same output
        
    Use cases:
        - Email lookup in database (indexed)
        - Verify data integrity
        - NOT for passwords (use bcrypt instead)
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


# =============================================================================
# HELPER: Mask sensitive data for display
# =============================================================================

def mask_email(email: str) -> str:
    """
    Mask email for safe display.
    
    Example:
        >>> mask_email("ujjwal@gmail.com")
        'uj****@gmail.com'
        
        >>> mask_email("ab@test.com")
        'a****@test.com'
    """
    if '@' not in email:
        return '****'
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = local[0] + '****'
    else:
        masked_local = local[:2] + '****'
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number for safe display.
    
    Example:
        >>> mask_phone("+919876543210")
        '+91****3210'
        
        >>> mask_phone("9876543210")
        '****3210'
    """
    if len(phone) <= 4:
        return '****'
    
    # Show last 4 digits
    return '****' + phone[-4:]
