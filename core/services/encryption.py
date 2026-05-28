"""Encryption service for sensitive data (passwords, API keys)."""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from bot.config import settings


class EncryptionService:
    """Service for encrypting/decrypting sensitive data."""

    def __init__(self):
        self._fernet = self._create_fernet()

    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from app secret key."""
        # Derive a proper key from the secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"v2ray-shop-bot-salt-2024",
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(settings.APP_SECRET_KEY.encode())
        )
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64 encoded ciphertext."""
        if not plaintext:
            return ""
        encrypted = self._fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64 encoded ciphertext."""
        if not ciphertext:
            return ""
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception:
            # If decryption fails, return as-is (might be unencrypted legacy data)
            return ciphertext

    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted (Fernet format)."""
        try:
            # Fernet tokens start with 'gAAAAA'
            return value.startswith("gAAAAA") and len(value) > 50
        except Exception:
            return False


# Singleton instance
encryption = EncryptionService()
