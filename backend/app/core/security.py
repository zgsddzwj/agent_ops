import hashlib
import secrets


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, hash, prefix)."""
    key = f"ao_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    prefix = key[:10]
    return key, key_hash, prefix


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
