"""Secret references: ``secrets://<provider>/<profile>`` (IMP-0015, Phase 1).

Registry entries and workload configs store only a reference; the value lives
in the OS keyring (service ``agent-os``, user ``<provider>/<profile>``) or in
the environment variable ``AGENT_OS_SECRET_<PROVIDER>_<PROFILE>`` (upper case,
non-alphanumerics -> ``_``), which wins so CI and containers work without a
keyring. Values are never returned by ``status``, never logged and never
written to Git -- only presence and the backing source are reported.

This generalizes the per-adapter ``key_env`` / ``keyring_user`` options in
adapters/http_api.py (which keep working) so new providers -- RunPod, Hugging
Face, a self-hosted OpenAI-compatible endpoint -- need no code change.
"""

from __future__ import annotations

import os
import re
from typing import Any

SCHEME = "secrets://"
KEYRING_SERVICE = "agent-os"
_PART = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def parse(ref: str) -> tuple[str, str]:
    """``secrets://runpod/default`` -> ("runpod", "default"). Profile defaults to ``default``."""
    if not isinstance(ref, str) or not ref.startswith(SCHEME):
        raise ValueError(f"not a secret reference (expected {SCHEME}<provider>/<profile>): {ref!r}")
    provider, _, profile = ref[len(SCHEME):].partition("/")
    provider, profile = provider.strip().lower(), (profile.strip().lower() or "default")
    for part in (provider, profile):
        if not _PART.match(part):
            raise ValueError(f"invalid secret reference part {part!r} in {ref!r}")
    return provider, profile


def env_var(ref: str) -> str:
    provider, profile = parse(ref)
    return "AGENT_OS_SECRET_" + re.sub(r"[^A-Z0-9]", "_", f"{provider}_{profile}".upper())


def keyring_user(ref: str) -> str:
    provider, profile = parse(ref)
    return f"{provider}/{profile}"


def _keyring():
    try:
        import keyring  # the project's existing dependency

        return keyring
    except Exception:
        return None


def resolve(ref: str) -> str | None:
    """The secret value, or None when it is not configured. Callers must not log it."""
    value = os.environ.get(env_var(ref))
    if value:
        return value.strip()
    backend = _keyring()
    if backend is None:
        return None
    try:
        stored = backend.get_password(KEYRING_SERVICE, keyring_user(ref))
    except Exception:
        return None
    return stored.strip() if stored else None


def status(ref: str) -> dict[str, Any]:
    """Presence and source only -- never the value."""
    source = None
    if os.environ.get(env_var(ref)):
        source = "environment"
    else:
        backend = _keyring()
        try:
            if backend is not None and backend.get_password(KEYRING_SERVICE, keyring_user(ref)):
                source = "keyring"
        except Exception:
            source = None
    return {"ref": ref, "configured": source is not None, "source": source, "env_var": env_var(ref),
            "keyring": f"{KEYRING_SERVICE}/{keyring_user(ref)}"}


def store(ref: str, value: str) -> dict[str, Any]:
    if not value or not value.strip():
        raise ValueError("refusing to store an empty secret")
    backend = _keyring()
    if backend is None:
        raise RuntimeError(f"no OS keyring available; set {env_var(ref)} in the environment instead")
    backend.set_password(KEYRING_SERVICE, keyring_user(ref), value.strip())
    return status(ref)


def delete(ref: str) -> dict[str, Any]:
    backend = _keyring()
    if backend is not None:
        try:
            backend.delete_password(KEYRING_SERVICE, keyring_user(ref))
        except Exception:
            pass
    return status(ref)


def redact(text: str, refs: list[str]) -> str:
    """Replace any resolved secret value that leaked into ``text``."""
    for ref in refs:
        value = resolve(ref)
        if value and len(value) >= 6:
            text = text.replace(value, f"<{ref}>")
    return text
