"""Bridge to the Ingester Engine, the canonical home of ingestion primitives.

Agent OS no longer carries its own ingestion ledger or document-extraction
cache; both live in ``unwit1/ingester-engine`` (``ingester_engine.ledger`` and
``ingester_engine.cache``). This module makes that package importable:

1. an installed distribution (``pip install -e <ingester-engine>``), else
2. ``INGESTER_ENGINE_ROOT``, else
3. the ``ingester-engine`` project checkout resolved through the Agent OS
   registry (``projects/registry.json`` + machine-local search roots).

It is imported by ``agent_os/__init__.py`` so every module can use plain
``from ingester_engine... import ...`` statements.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

PROJECT_ID = "ingester-engine"


class IngesterEngineUnavailable(ImportError):
    pass


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    configured = os.environ.get("INGESTER_ENGINE_ROOT")
    if configured:
        roots.append(Path(configured).expanduser())
    try:
        from .machine import resolve_path
        from .storage import load_json
        from .paths import ROOT

        registry = load_json(ROOT / "projects" / "registry.json")
        entry = next((item for item in registry.get("projects", []) if item.get("id") == PROJECT_ID), None)
        if entry is not None:
            path, _ = resolve_path(entry)
            roots.append(Path(path))
    except Exception:  # noqa: BLE001 - discovery is best effort; the error below explains
        pass
    return roots


def ensure_ingester_engine() -> None:
    if importlib.util.find_spec("ingester_engine") is not None:
        return
    for root in _candidate_roots():
        source = root / "src"
        if (source / "ingester_engine" / "__init__.py").is_file():
            sys.path.insert(0, str(source))
            os.environ.setdefault("INGESTER_ENGINE_ROOT", str(root))
            return
    raise IngesterEngineUnavailable(
        "Agent OS needs the Ingester Engine (unwit1/ingester-engine). Clone it next to this repository "
        "and run `pip install -e <ingester-engine>`, or set INGESTER_ENGINE_ROOT."
    )
