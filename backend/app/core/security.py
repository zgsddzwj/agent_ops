import hashlib
import hmac
import secrets


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, hash, prefix).

    The full key should be shown to the user exactly once;
    store only the hash and prefix in the database.
    """
    key = f"ao_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    prefix = key[:10]
    return key, key_hash, prefix


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash using constant-time comparison.

    Uses hmac.compare_digest to prevent timing attacks that could reveal
    information about the hash character by character.
    """
    computed_hash = hashlib.sha256(key.encode()).hexdigest()
    return hmac.compare_digest(computed_hash, stored_hash)
