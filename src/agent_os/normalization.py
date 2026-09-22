"""Small deterministic text normalization primitives."""

from __future__ import annotations

import re


def normalise_text(value: str) -> str:
    """Return lowercase ASCII-alphanumeric tokens joined by single spaces."""

    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))
