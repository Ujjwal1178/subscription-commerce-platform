"""Encryption Utilities - AES-256 for PII, SHA256 for indexed lookups."""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


def _get_encryption_key() -> bytes:
    """Get 32-byte encryption key from environment."""
    key = os.environ.get('ENCRYPTION_KEY', 'dev-key-32-bytes-long-exactly!!')
    key_bytes = key.encode('utf-8')
    if len(key_bytes) != 32:
        raise ValueError(f"ENCRYPTION_KEY must be exactly 32 bytes, got {len(key_bytes)}")
    return key_bytes


def encrypt_data(plaintext: str) -> str:
    """Encrypt data using AES-256-CBC. Returns Base64 encoded IV+Ciphertext."""
    key = _get_encryption_key()
    iv = os.urandom(16)
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
    
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode('utf-8')


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt AES-256-CBC encrypted data. Returns original plaintext."""
    key = _get_encryption_key()
    combined = base64.b64decode(encrypted_data.encode('utf-8'))
    
    iv, ciphertext = combined[:16], combined[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_data) + unpadder.finalize()
    
    return plaintext.decode('utf-8')


def generate_hash(data: str) -> str:
    """Generate SHA256 hash. Returns 64-char hex string. Same input = same output."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def mask_email(email: str) -> str:
    """Mask email for display. Example: ujjwal@gmail.com -> uj****@gmail.com"""
    if '@' not in email:
        return '****'
    local, domain = email.split('@', 1)
    masked = local[:2] + '****' if len(local) > 2 else local[0] + '****'
    return f"{masked}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone for display. Example: +919876543210 -> ****3210"""
    return '****' + phone[-4:] if len(phone) > 4 else '****'
