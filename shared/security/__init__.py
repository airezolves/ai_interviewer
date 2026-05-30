"""Cryptography helpers — AES-256-GCM with PBKDF2-SHA512 key derivation.

Wire-compatible with the Node.js EncryptionService used in the reference
model_factory.py: SALT(64) || IV(16) || TAG(16) || CIPHERTEXT, base64-encoded.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


_SALT_LEN = 64
_IV_LEN = 16
_TAG_LEN = 16
_KEY_LEN = 32
_ITERATIONS = 100_000


def _derive_key(master_key: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=_KEY_LEN,
        salt=salt,
        iterations=_ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(master_key.encode())


def encrypt_secret(plaintext: str, master_key: str) -> str:
    """Encrypt `plaintext` with AES-256-GCM and return base64-encoded blob."""
    if not master_key:
        raise ValueError("master_key required for encryption")
    salt = os.urandom(_SALT_LEN)
    iv = os.urandom(_IV_LEN)
    key = _derive_key(master_key, salt)
    encryptor = Cipher(
        algorithms.AES(key), modes.GCM(iv), backend=default_backend()
    ).encryptor()
    ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()
    blob = salt + iv + encryptor.tag + ciphertext
    return base64.b64encode(blob).decode("ascii")


def decrypt_secret(ciphertext_b64: str, master_key: str) -> str:
    """Decrypt a base64-encoded AES-256-GCM blob back to plaintext."""
    if not master_key:
        raise ValueError("master_key required for decryption")
    data = base64.b64decode(ciphertext_b64)
    salt = data[:_SALT_LEN]
    iv = data[_SALT_LEN : _SALT_LEN + _IV_LEN]
    tag = data[_SALT_LEN + _IV_LEN : _SALT_LEN + _IV_LEN + _TAG_LEN]
    ciphertext = data[_SALT_LEN + _IV_LEN + _TAG_LEN :]
    key = _derive_key(master_key, salt)
    decryptor = Cipher(
        algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()
    ).decryptor()
    return (decryptor.update(ciphertext) + decryptor.finalize()).decode("utf-8")


def mask_secret(plaintext: str, visible: int = 4) -> str:
    """Return a masked preview (e.g. '••••••sk-9c2f') for safe API responses."""
    if not plaintext:
        return ""
    tail = plaintext[-visible:] if len(plaintext) > visible else plaintext
    return "•" * 8 + tail
