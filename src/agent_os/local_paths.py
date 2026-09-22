"""Deterministic privacy checks for workstation-local runtime paths."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .paths import ROOT


def is_gitignored_local_path(
    path: Path,
    *,
    allowed_roots: Iterable[str] = (".agent-local",),
    repository_root: Path = ROOT,
) -> bool:
    """Return whether ``path`` is outside Git or under an allowed ignored root.

    Callers retain responsibility for their domain-specific exception and
    message.  ``allowed_roots`` is explicit because local stores may have
    different, established privacy boundaries.
    """

    resolved = Path(path).expanduser().resolve()
    try:
        relative = resolved.relative_to(Path(repository_root).resolve())
    except ValueError:
        return True
    first = relative.parts[0] if relative.parts else ""
    return first in set(allowed_roots)
