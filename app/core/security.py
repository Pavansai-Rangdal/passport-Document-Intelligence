"""Security utilities for encryption, hashing, and access control."""

import hashlib
import hmac
import secrets
from base64 import urlsafe_b64encode
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings
from app.core.exceptions import SecurityError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityManager:
    """Manages encryption, hashing, and security operations."""

    def __init__(self) -> None:
        settings = get_settings()
        self._fernet: Fernet | None = None
        self._secret_key = settings.secret_key.encode()
        self._encryption_key = settings.encryption_key.encode()

    @property
    def fernet(self) -> Fernet:
        """Lazy initialization of Fernet cipher."""
        if self._fernet is None:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"passport_di_salt",
                iterations=100000,
            )
            key = urlsafe_b64encode(kdf.derive(self._encryption_key))
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            raise SecurityError("Failed to encrypt data") from e

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise SecurityError("Failed to decrypt data") from e

    def hash_sha256(self, data: str) -> str:
        """Generate SHA-256 hash."""
        return hashlib.sha256(data.encode()).hexdigest()

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)

    def verify_hmac(self, data: str, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = hmac.new(
            self._secret_key,
            data.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def generate_hmac(self, data: str) -> str:
        """Generate HMAC signature."""
        return hmac.new(
            self._secret_key,
            data.encode(),
            hashlib.sha256,
        ).hexdigest()

    def redact_sensitive_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive fields from dictionaries."""
        sensitive_keys = {
            "document_number",
            "passport_number",
            "national_id",
            "ssn",
            "birth_date",
            "expiry_date",
        }
        redacted = data.copy()
        for key in sensitive_keys:
            if key in redacted and redacted[key]:
                value = str(redacted[key])
                if len(value) > 4:
                    redacted[key] = f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
                else:
                    redacted[key] = "****"
        return redacted


_security_manager: SecurityManager | None = None


def get_security_manager() -> SecurityManager:
    """Get singleton security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager
