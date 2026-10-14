"""Paths for OpenAI-compatible HTTP endpoints."""

from __future__ import annotations

import re
from urllib.parse import urlsplit


PATH_STYLES = ("auto", "append_v1", "root")

_VERSION = re.compile(r"^v\d+(alpha|beta)?\d*$")
_PATHS = {
    "chat": "/chat/completions",
    "models": "/models",
    "embeddings": "/embeddings",
    "rerank": "/rerank",
    "images": "/images/generations",
    "transcriptions": "/audio/transcriptions",
    "speech": "/audio/speech",
}


def validate_base_url(base_url: str) -> None:
    """Require a plain HTTP(S) origin or path without URL credentials."""
    if not isinstance(base_url, str):
        raise ValueError("base URL must be an http:// or https:// URL")
    try:
        parsed = urlsplit(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or not parsed.hostname:
            raise ValueError("base URL must be an http:// or https:// URL with a host")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("base URL must not contain credentials")
    except ValueError as exc:
        if str(exc).startswith("base URL"):
            raise
        raise ValueError(f"invalid base URL: {exc}") from exc
    if "?" in base_url or "#" in base_url:
        raise ValueError("base URL must not contain a query or fragment")


def api_root(base_url: str, path_style: str = "auto") -> str:
    """Resolve the API root while preserving an explicit version suffix."""
    validate_base_url(base_url)
    if path_style not in PATH_STYLES:
        raise ValueError(f"path_style must be one of {PATH_STYLES}")
    base = base_url.rstrip("/")
    if path_style == "root" or (path_style == "auto" and _VERSION.fullmatch(urlsplit(base).path.rsplit("/", 1)[-1])):
        return base
    return base + "/v1"


def url(base_url: str, kind: str, path_style: str = "auto", overrides: dict[str, str] | None = None) -> str:
    """Build a request URL, optionally replacing one resource path."""
    if kind not in _PATHS:
        raise ValueError(f"unknown endpoint kind {kind!r}")
    root = api_root(base_url, path_style)
    override = (overrides or {}).get(kind)
    if override is None:
        return root + _PATHS[kind]
    if not isinstance(override, str):
        raise ValueError(f"endpoint override for {kind!r} must be a URL or absolute path")
    if override.startswith(("http://", "https://")):
        return override
    if override.startswith("/"):
        return root + override
    raise ValueError(f"endpoint override for {kind!r} must be a URL or path beginning with '/'")
