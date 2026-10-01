"""Model Research Radar v1: discover open-weight models into a local catalog (IMP-0015).

Roadmap acceptance 11: discover a new release, record provenance, license,
hardware and size metadata, and queue an eval -- without rewriting core code.

Source: the Hugging Face Hub REST listing (prior art PA-hf-hub, BORROW, stdlib
client). Scans are declarative (``DEFAULT_SCANS`` or CLI flags), covering
text/code, vision-language, image generation/editing, ASR, TTS, audio and
embeddings. Each candidate is normalized to the capability-registry shape:
exact ``model_id`` + ``revision`` (commit sha), pipeline -> modalities and
capabilities, license, base model, quantization hints, parameter count,
popularity and a *declared* refusal profile hint from tags (``abliterated`` /
``uncensored``) -- a behavioural label, never a quality score.

The catalog lives at ``<orchestrator home>/model-catalog.json`` (local, not
Git). New models and new revisions of known models are reported; candidates
with a known license and enough adoption are appended to
``<home>/eval-queue.jsonl`` with suggested suites. Nothing downloads weights,
and public benchmark claims are not imported as evidence: measured Agent OS
evals decide routing (roadmap invariant 7).
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

from ..timestamps import utc_now_iso
from .store import orchestrator_home

HUB_API = "https://huggingface.co/api/models"
HF_SECRET = "secrets://huggingface/default"  # optional: rate limits, gated repos
EXPAND = ("cardData", "safetensors", "sha", "lastModified", "pipeline_tag", "downloads", "likes", "tags", "createdAt", "library_name")
# pipeline tag -> (modalities, capabilities)
PIPELINES: dict[str, tuple[list[str], list[str]]] = {
    "text-generation": (["text", "code"], ["reasoning"]),
    "image-text-to-text": (["multimodal", "vision", "text"], ["vision"]),
    "text-to-image": (["image"], ["image_generation"]),
    "image-to-image": (["image"], ["image_editing"]),
    "automatic-speech-recognition": (["audio"], ["asr"]),
    "text-to-speech": (["audio"], ["tts"]),
    "text-to-audio": (["audio"], ["audio_generation"]),
    "audio-to-audio": (["audio"], ["speech_to_speech", "audio_enhancement"]),
    "feature-extraction": (["embedding"], ["embedding"]),
    "sentence-similarity": (["embedding"], ["embedding"]),
    "text-classification": (["text"], ["classification"]),
}
DEFAULT_SCANS = [
    {"name": "text-generation-trending", "pipeline_tag": "text-generation", "sort": "trendingScore", "limit": 20},
    {"name": "abliterated", "search": "abliterated", "sort": "downloads", "limit": 20},
    {"name": "vision-language", "pipeline_tag": "image-text-to-text", "sort": "trendingScore", "limit": 10},
    {"name": "image-generation", "pipeline_tag": "text-to-image", "sort": "trendingScore", "limit": 10},
    {"name": "asr", "pipeline_tag": "automatic-speech-recognition", "sort": "trendingScore", "limit": 10},
    {"name": "tts", "pipeline_tag": "text-to-speech", "sort": "trendingScore", "limit": 10},
]
QUANT_TAGS = ("gguf", "awq", "gptq", "exl2", "mlx", "fp8", "int4", "int8", "2-bit", "4-bit", "8-bit", "bitsandbytes")
SUITES_BY_MODALITY = {"text": ["EVS-CAPABILITY-CLASSIFICATION", "EVS-CONTEXT"], "code": ["EVS-TEST-SELECTION"], "vision": [], "image": [], "audio": [], "embedding": []}


def catalog_path(home: Path | None = None) -> Path:
    return Path(home or orchestrator_home()) / "model-catalog.json"


def queue_path(home: Path | None = None) -> Path:
    return Path(home or orchestrator_home()) / "eval-queue.jsonl"


def scan_url(scan: dict[str, Any]) -> str:
    params: list[tuple[str, str]] = [("sort", str(scan.get("sort") or "downloads")), ("limit", str(int(scan.get("limit") or 20)))]
    for key in ("search", "pipeline_tag", "author", "filter"):
        if scan.get(key):
            params.append((key, str(scan[key])))
    params += [("expand[]", item) for item in EXPAND]
    return f"{HUB_API}?{urllib.parse.urlencode(params)}"


def normalize(item: dict[str, Any], scan_name: str, fetched_at: str) -> dict[str, Any] | None:
    model_id = item.get("id") or item.get("modelId")
    if not model_id:
        return None
    tags = [str(tag) for tag in item.get("tags") or []]
    lowered = {tag.lower() for tag in tags}
    card = item.get("cardData") if isinstance(item.get("cardData"), dict) else {}
    license_ = card.get("license") or next((tag.split(":", 1)[1] for tag in tags if tag.startswith("license:")), None)
    base = card.get("base_model") or next((tag.split(":", 1)[1] for tag in tags if tag.startswith("base_model:") and tag.count(":") == 1), None)
    pipeline = item.get("pipeline_tag")
    modalities, capabilities = PIPELINES.get(str(pipeline), (["text"] if pipeline is None else [], []))
    refusal = "abliterated" if "abliterated" in lowered else "low" if lowered & {"uncensored", "unfiltered"} else "unknown"
    safetensors = item.get("safetensors") if isinstance(item.get("safetensors"), dict) else {}
    return {
        "model_id": str(model_id),
        "revision": item.get("sha"),
        "pipeline": pipeline,
        "library": item.get("library_name"),
        "modalities": modalities,
        "capabilities": capabilities,
        "license": str(license_) if license_ else None,
        "base_model": base if isinstance(base, str) else (base[0] if isinstance(base, list) and base else None),
        "quantization": sorted(tag for tag in QUANT_TAGS if tag in lowered),
        "parameters": safetensors.get("total"),
        "refusal_profile_hint": refusal,
        "downloads": item.get("downloads"),
        "likes": item.get("likes"),
        "created_at": item.get("createdAt"),
        "last_modified": item.get("lastModified"),
        "provenance": {"source": "huggingface_hub", "url": f"https://huggingface.co/{model_id}", "scan": scan_name, "fetched_at": fetched_at},
    }


def fetch(scan: dict[str, Any], opener: Callable[..., Any] | None = None) -> list[dict[str, Any]]:
    headers = {"user-agent": "agent-os/1", "accept": "application/json"}
    from .secret_refs import resolve

    token = resolve(HF_SECRET)
    if token:
        headers["authorization"] = f"Bearer {token}"
    request = urllib.request.Request(scan_url(scan), headers=headers)
    with (opener or urllib.request.urlopen)(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    return payload if isinstance(payload, list) else []


def eval_candidate(model: dict[str, Any], min_downloads: int) -> str | None:
    """Why a catalog entry should be queued for an Agent OS eval, or None."""
    if not model.get("license"):
        return None
    if (model.get("downloads") or 0) < min_downloads:
        return None
    if not model.get("modalities"):
        return None
    return f"license {model['license']}, {model.get('downloads')} downloads, pipeline {model.get('pipeline')}"


def scan(scans: list[dict[str, Any]] | None = None, *, home: Path | None = None, opener: Callable[..., Any] | None = None,
         min_downloads: int = 10000, queue: bool = True, pause: float = 0.2) -> dict[str, Any]:
    """Run scans, merge into the local catalog, report new models/revisions,
    queue eval candidates. Network errors are reported per scan."""
    from ..storage import write_json

    scans = scans or DEFAULT_SCANS
    path = catalog_path(home)
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        catalog = {"schema": "personal-agent/model-catalog/v1", "models": {}}
    models: dict[str, Any] = catalog.setdefault("models", {})
    fetched_at = utc_now_iso()
    new, revised, errors, seen = [], [], [], 0
    for index, item in enumerate(scans):
        if index and pause:
            time.sleep(pause)
        try:
            rows = fetch(item, opener)
        except Exception as exc:
            errors.append({"scan": item.get("name"), "error": f"{type(exc).__name__}: {str(exc)[:160]}"})
            continue
        for row in rows:
            model = normalize(row, str(item.get("name") or "scan"), fetched_at)
            if model is None:
                continue
            seen += 1
            previous = models.get(model["model_id"])
            if previous is None:
                new.append(model["model_id"])
                model["first_seen"] = fetched_at
            else:
                model["first_seen"] = previous.get("first_seen", fetched_at)
                if previous.get("revision") and model.get("revision") and previous["revision"] != model["revision"]:
                    revised.append(model["model_id"])
            models[model["model_id"]] = model
    catalog["updated_at"] = fetched_at
    write_json(path, catalog)
    queued = []
    if queue:
        target = queue_path(home)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            for model_id in [*new, *revised]:
                model = models[model_id]
                reason = eval_candidate(model, min_downloads)
                if not reason:
                    continue
                suites = sorted({suite for modality in model["modalities"] for suite in SUITES_BY_MODALITY.get(modality, [])})
                entry = {"at": fetched_at, "model_id": model_id, "revision": model.get("revision"), "reason": reason,
                         "modalities": model["modalities"], "suggested_suites": suites, "status": "queued"}
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
                queued.append(model_id)
    return {"catalog": str(path), "models_seen": seen, "catalog_size": len(models), "new": new, "new_revisions": revised,
            "queued_for_eval": queued, "errors": errors}


def merge_free_catalog(snapshot: dict[str, Any], *, home: Path | None = None) -> dict[str, Any]:
    """Merge OpenRouter free models snapshot into the radar catalog.

    Upserts free models from snapshot, tagging with source='openrouter-free' and
    last_seen/last_verified timestamps. Marks free models removed from the snapshot
    as unavailable (available=False) instead of deleting them. Queues newly added
    free models as eval candidates."""
    from ..storage import write_json

    path = catalog_path(home)
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        catalog = {"schema": "personal-agent/model-catalog/v1", "models": {}}

    models: dict[str, Any] = catalog.setdefault("models", {})
    fetched_at = snapshot.get("fetched_at") or utc_now_iso()
    new, seen, errors = [], 0, []

    # Validate snapshot has models
    snapshot_models = snapshot.get("models")
    if not isinstance(snapshot_models, list) or not snapshot_models:
        errors.append({"snapshot": "Invalid or empty models list in snapshot"})
        return {
            "catalog": str(path),
            "models_seen": 0,
            "catalog_size": len(models),
            "new": [],
            "queued_for_eval": [],
            "errors": errors,
        }

    # Track which slugs are in this snapshot
    snapshot_slugs = set()

    # Identify models from openrouter-free source before this merge
    free_model_ids_before = {k for k, m in models.items() if (m.get("provenance") or {}).get("source") == "openrouter-free"}

    # Process models from snapshot
    for item in snapshot_models:
        if not isinstance(item, dict) or not item.get("slug"):
            continue

        seen += 1
        model_id = item["slug"]
        snapshot_slugs.add(model_id)

        # Check if model already exists and is from another source
        existing = models.get(model_id)
        if existing and (existing.get("provenance") or {}).get("source") != "openrouter-free":
            # Skip overwriting models from other sources
            continue

        # Flatten modalities from input/output dicts to sorted list
        modalities = []
        if isinstance(item.get("modalities"), dict):
            input_mods = item["modalities"].get("input", []) or []
            output_mods = item["modalities"].get("output", []) or []
            modalities = sorted(set(input_mods + output_mods))

        # Build radar catalog entry for free model
        model = {
            "model_id": model_id,
            "revision": item.get("canonical_slug") or item.get("revision"),
            "modalities": modalities,
            "capabilities": [],
            "context_length": item.get("context_length"),
            "supports_tools": item.get("supports_tools", False),
            "supports_structured_output": item.get("supports_structured_output", False),
            "pricing": item.get("pricing", {}),
            "provenance": {
                "source": "openrouter-free",
                "provider": snapshot.get("provider", "openrouter"),
                "catalog_version": snapshot.get("catalog_version"),
                "fetched_at": fetched_at,
            },
            "last_seen": fetched_at,
            "last_verified": fetched_at,
        }

        # Preserve first_seen from existing entry
        if model_id in models:
            model["first_seen"] = models[model_id].get("first_seen", fetched_at)
        else:
            model["first_seen"] = fetched_at
            new.append(model_id)

        models[model_id] = model

    # Mark removed free models as unavailable instead of deleting
    for model_id in free_model_ids_before - snapshot_slugs:
        if model_id in models:
            existing_model = models[model_id]
            # Skip if already marked unavailable
            if existing_model.get("available") is False:
                continue
            existing_model["available"] = False
            # Add unavailable_since only if not already set
            if "unavailable_since" not in existing_model:
                existing_model["unavailable_since"] = fetched_at

    catalog["updated_at"] = fetched_at
    write_json(path, catalog)

    # Queue newly added free models for evaluation
    queued = []
    if new:
        target = queue_path(home)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            for model_id in new:
                model = models[model_id]
                reason = f"free tier OpenRouter model, context_length {model.get('context_length')}"
                suites = sorted({
                    suite for modality in model["modalities"]
                    for suite in SUITES_BY_MODALITY.get(modality, [])
                })
                entry = {
                    "at": fetched_at,
                    "model_id": model_id,
                    "revision": model.get("revision"),
                    "reason": reason,
                    "modalities": model["modalities"],
                    "suggested_suites": suites,
                    "status": "queued"
                }
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
                queued.append(model_id)

    return {
        "catalog": str(path),
        "models_seen": seen,
        "catalog_size": len(models),
        "new": new,
        "queued_for_eval": queued,
        "errors": errors,
    }


def catalog_summary(home: Path | None = None, *, modality: str | None = None, refusal_profile: str | None = None, limit: int = 25) -> dict[str, Any]:
    try:
        catalog = json.loads(catalog_path(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"models": [], "catalog_size": 0}
    rows = list((catalog.get("models") or {}).values())
    if modality:
        rows = [row for row in rows if modality in (row.get("modalities") or [])]
    if refusal_profile:
        rows = [row for row in rows if row.get("refusal_profile_hint") == refusal_profile]
    rows.sort(key=lambda row: -(row.get("downloads") or 0))
    keys = ("model_id", "revision", "pipeline", "license", "parameters", "quantization", "refusal_profile_hint", "downloads", "last_modified")
    return {"catalog_size": len(catalog.get("models") or {}), "matched": len(rows), "models": [{key: row.get(key) for key in keys} for row in rows[:limit]]}
