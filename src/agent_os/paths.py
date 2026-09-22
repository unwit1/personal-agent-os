from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "projects" / "registry.json"
INDEX_DIR = ROOT / ".agent-os"
INDEX_PATH = INDEX_DIR / "index.sqlite"


def project_collection_dir(
    project_id: str,
    collection: str,
    *,
    root: Path = ROOT,
) -> Path:
    """Return the canonical Git-backed directory for a project collection."""

    return root / "projects" / project_id / collection
