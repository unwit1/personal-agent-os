"""Small deterministic hashing/fingerprint primitives."""

from __future__ import annotations

import hashlib
from typing import Iterable


def nul_joined_sha256(parts: Iterable[str], length: int | None = None) -> str:
    """Hash null-joined parts with SHA256, optionally truncating the hex digest.

    Args:
        parts: Iterable of strings to join with null bytes and hash.
        length: If provided, truncate hex digest to this many characters (1-64).
                If None, return full 64-character hex digest.

    Returns:
        SHA256 hex digest, truncated to length if specified.

    Raises:
        ValueError: If length is not None and not in range [1, 64].
    """
    if length is not None and not (1 <= length <= 64):
        raise ValueError(f"length must be in range [1, 64], got {length}")

    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()
    return digest[:length] if length is not None else digest
