"""Artifact manifests for models, adapters, checkpoints and outputs (IMP-0015).

Roadmap acceptance 8: LoRA/adaptation jobs retain reproducible manifests and
resumable checkpoints. A manifest records *what* an artifact is and *how* it
was produced -- never the artifact bytes or private data, which stay in local
or provider storage. Manifests may be stored under .agent-local or attached to
run records; the ``uri`` may point to local disk or provider storage.

``build`` validates and fingerprints a manifest; ``verify`` checks a local
file against its recorded sha256 so a resumed job does not continue from a
corrupted or swapped checkpoint.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..timestamps import utc_now_iso

SCHEMA = "personal-agent/artifact-manifest/v1"
KINDS = ("model", "adapter", "checkpoint", "dataset", "output", "audio", "image")


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(
    kind: str,
    uri: str,
    *,
    sha256: str | None = None,
    size_bytes: int | None = None,
    base_model: str | None = None,
    base_revision: str | None = None,
    parent: str | None = None,
    training_config: dict[str, Any] | None = None,
    license: str | None = None,
    job_id: str | None = None,
    step: int | None = None,
) -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError(f"artifact kind must be one of {KINDS}")
    if not uri:
        raise ValueError("uri is required")
    if kind in {"adapter", "checkpoint"} and not (base_model and base_revision):
        raise ValueError(f"{kind} manifests need base_model and base_revision to be reproducible")
    if sha256 is not None and (len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256.lower())):
        raise ValueError("sha256 must be 64 hex characters")
    config_digest = hashlib.sha256(json.dumps(training_config, sort_keys=True).encode()).hexdigest()[:16] if training_config else None
    manifest = {
        "schema": SCHEMA, "kind": kind, "uri": uri, "sha256": sha256.lower() if sha256 else None, "size_bytes": size_bytes,
        "base_model": base_model, "base_revision": base_revision, "parent": parent, "training_config": training_config,
        "training_config_digest": config_digest, "license": license, "job_id": job_id, "step": step, "created_at": utc_now_iso(),
    }
    identity = {key: manifest[key] for key in ("kind", "uri", "sha256", "base_model", "base_revision", "parent", "training_config_digest", "step")}
    manifest["id"] = "ART-" + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:12]
    return manifest


def verify(manifest: dict[str, Any], path: str | Path) -> dict[str, Any]:
    """Compare a local file with the manifest's sha256 (and size, if recorded)."""
    if not manifest.get("sha256"):
        return {"ok": False, "reason": "manifest has no sha256"}
    target = Path(path)
    if not target.is_file():
        return {"ok": False, "reason": f"missing file {target.name}"}
    if manifest.get("size_bytes") is not None and target.stat().st_size != manifest["size_bytes"]:
        return {"ok": False, "reason": "size mismatch"}
    actual = file_sha256(target)
    return {"ok": actual == manifest["sha256"], "reason": None if actual == manifest["sha256"] else "sha256 mismatch"}


def latest_resumable(manifests: list[dict[str, Any]], job_id: str) -> dict[str, Any] | None:
    """Newest checkpoint of a job, by step, for resume after preemption."""
    checkpoints = [item for item in manifests if item.get("kind") == "checkpoint" and item.get("job_id") == job_id and item.get("step") is not None]
    return max(checkpoints, key=lambda item: item["step"]) if checkpoints else None
