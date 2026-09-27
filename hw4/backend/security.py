"""Hash and verify shopper passwords, and mint the signed session tokens the site sends back.

Passwords are stored as bcrypt digests, never as plain text and never as a bare hash of
the password. Verification also accepts the other formats a seeded pack might ship so the
provided test account still logs in.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time

import bcrypt

TOKEN_TTL_SECONDS = 60 * 60 * 12
PBKDF2_ROUNDS = 240_000

_secret_cache: bytes | None = None


def secret_key() -> bytes:
    """Use SESSION_SECRET when set; otherwise mint one per process so tokens still work."""
    global _secret_cache
    if _secret_cache is None:
        configured = os.getenv("SESSION_SECRET", "").strip()
        _secret_cache = configured.encode("utf-8") if configured else secrets.token_bytes(32)
    return _secret_cache


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def pbkdf2_digest(password: str, salt: str) -> str:
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt}${base64.b64encode(derived).decode('ascii')}"


def verify_password(password: str, stored: str) -> bool:
    """Accept bcrypt, PBKDF2, a hex digest, or (last resort) a plain-text seed value."""
    if not stored:
        return False
    candidate = password.encode("utf-8")

    if stored.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(candidate, stored.encode("utf-8"))
        except ValueError:
            return False

    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds, salt, _ = stored.split("$", 3)
        except ValueError:
            return False
        derived = hashlib.pbkdf2_hmac("sha256", candidate, salt.encode("utf-8"), int(rounds))
        expected = stored.rsplit("$", 1)[-1]
        return hmac.compare_digest(base64.b64encode(derived).decode("ascii"), expected)

    lowered = stored.strip().lower()
    if len(lowered) == 64 and all(char in "0123456789abcdef" for char in lowered):
        return hmac.compare_digest(hashlib.sha256(candidate).hexdigest(), lowered)
    if len(lowered) == 32 and all(char in "0123456789abcdef" for char in lowered):
        return hmac.compare_digest(hashlib.md5(candidate).hexdigest(), lowered)

    return hmac.compare_digest(stored, password)


def needs_rehash(stored: str) -> bool:
    """True when a pack stored the password in a weaker format than the one we write."""
    return not stored.startswith(("$2a$", "$2b$", "$2y$"))


def issue_token(user_id: int) -> str:
    payload = f"{user_id}:{int(time.time()) + TOKEN_TTL_SECONDS}"
    signature = hmac.new(secret_key(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode("ascii")


def read_token(token: str) -> int | None:
    """Return the user id inside a signed, unexpired token, or None when it fails a check."""
    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        user_id, expires_at, signature = decoded.rsplit(":", 2)
    except (ValueError, UnicodeDecodeError):
        return None
    payload = f"{user_id}:{expires_at}"
    expected = hmac.new(secret_key(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    if int(expires_at) < int(time.time()):
        return None
    return int(user_id)
