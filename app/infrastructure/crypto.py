"""Encryption utilities for secure backup storage."""

from __future__ import annotations

import base64
import logging
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_file(source_path: str, dest_path: str, password: str) -> bool:
    """Encrypt a file with a password."""
    try:
        salt = os.urandom(16)
        key = derive_key(password, salt)
        fernet = Fernet(key)

        with open(source_path, "rb") as source_file:
            data = source_file.read()

        encrypted = fernet.encrypt(data)

        with open(dest_path, "wb") as dest_file:
            dest_file.write(salt)
            dest_file.write(encrypted)

        logger.info("File encrypted: %s", dest_path)
        return True
    except Exception as exc:
        logger.error("Encryption failed: %s", exc)
        return False


def decrypt_file(source_path: str, dest_path: str, password: str) -> bool:
    """Decrypt a file with a password."""
    try:
        with open(source_path, "rb") as source_file:
            salt = source_file.read(16)
            encrypted = source_file.read()

        key = derive_key(password, salt)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted)

        with open(dest_path, "wb") as dest_file:
            dest_file.write(decrypted)

        logger.info("File decrypted: %s", dest_path)
        return True
    except Exception as exc:
        logger.error("Decryption failed: %s", exc)
        return False
