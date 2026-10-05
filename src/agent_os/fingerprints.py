"""Small deterministic hashing/fingerprint primitives."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Iterable


def _truncate(digest: str, length: int | None) -> str:
    """Validate and truncate a hex digest to the specified length.

    Args:
        digest: Hex digest string (64 characters for SHA256).
        length: If provided, truncate to this many characters (1-64).
                If None, return full digest.

    Returns:
        Hex digest, truncated to length if specified.

    Raises:
        ValueError: If length is not None and not in range [1, 64].
    """
    if length is not None and not (1 <= length <= 64):
        raise ValueError(f"length must be in range [1, 64], got {length}")
    return digest[:length] if length is not None else digest


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
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()
    return _truncate(digest, length)


def text_sha256(text: str, length: int | None = None) -> str:
    """Hash UTF-8 text with SHA256, optionally truncating the hex digest.

    Args:
        text: String to hash.
        length: If provided, truncate hex digest to this many characters (1-64).
                If None, return full 64-character hex digest.

    Returns:
        SHA256 hex digest, truncated to length if specified.

    Raises:
        ValueError: If length is not None and not in range [1, 64].
    """
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return _truncate(digest, length)


def json_sha256(
    value: Any,
    length: int | None = None,
    *,
    sort_keys: bool = True,
    ensure_ascii: bool = True,
    default: Callable[[Any], Any] | None = None,
) -> str:
    """Hash JSON representation with SHA256, optionally truncating the hex digest.

    Args:
        value: Value to serialize to JSON and hash.
        length: If provided, truncate hex digest to this many characters (1-64).
                If None, return full 64-character hex digest.
        sort_keys: If True, sort dictionary keys in JSON output.
        ensure_ascii: If True, escape non-ASCII characters in JSON output.
        default: Callable to serialize objects that are not otherwise serializable.

    Returns:
        SHA256 hex digest, truncated to length if specified.

    Raises:
        ValueError: If length is not None and not in range [1, 64].
    """
    json_str = json.dumps(
        value, sort_keys=sort_keys, ensure_ascii=ensure_ascii, default=default
    )
    digest = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    return _truncate(digest, length)
