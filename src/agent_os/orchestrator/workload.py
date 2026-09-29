"""Provider-neutral workload contract (IMP-0015, Phase 0).

Every execution request -- a text/code inference, an image edit, an ASR batch,
a LoRA run -- normalizes to one workload object, so new modalities and
providers need no scheduler change (roadmap acceptance 1-2, 9). The workload
feeds routing (``to_requirements``), quoting (quote.py) and budget gates.

Sensitivity maps to deployment requirements explicitly, never by guess:

* ``secret``   -> deployment in {local}
* ``private``  -> deployment in {local, gpu_pod, serverless} (self-hosted weights)
* ``internal`` / ``public`` -> no deployment constraint

These are defaults the operator can tighten by passing explicit
``requirements``; a workload can never loosen its sensitivity mapping.
"""

from __future__ import annotations

from typing import Any

from .model_profile import MODALITIES, normalize_requirements

SCHEMA = "personal-agent/workload/v1"
WORKLOAD_TYPES = ("inference", "batch_inference", "embedding", "training", "fine_tune", "adapter_training", "evaluation", "conversion", "serving")
TRAINING_TYPES = frozenset({"training", "fine_tune", "adapter_training"})
SENSITIVITY = ("public", "internal", "private", "secret")
SENSITIVITY_DEPLOYMENTS = {"secret": ["local"], "private": ["local", "gpu_pod", "serverless"]}
# Modality-specific capabilities (roadmap: capability registry). Free-form
# capabilities are allowed; these are the recognized ones for validation hints.
KNOWN_CAPABILITIES = frozenset({
    "coding", "reasoning", "planning", "tool_calling", "structured_output",
    "image_generation", "image_editing", "vision",
    "asr", "tts", "speech_to_speech", "voice_conversion", "diarization", "audio_enhancement", "alignment", "audio_generation",
    "embedding", "classification", "lora", "full_finetune",
})
SIZE_KEYS = ("input_tokens", "output_tokens", "items", "images", "audio_seconds", "dataset_tokens", "epochs")
RESOURCE_KEYS = ("vram_gb", "ram_gb", "storage_gb", "gpus")


def _positive(value: Any, key: str) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number") from exc
    if number < 0:
        raise ValueError(f"{key} must be >= 0")
    return number


def normalize_workload(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("workload must be an object")
    kind = str(raw.get("type") or "inference")
    if kind not in WORKLOAD_TYPES:
        raise ValueError(f"workload type must be one of {WORKLOAD_TYPES}")
    modalities = raw.get("modalities") or raw.get("modality") or ["text"]
    modalities = [modalities] if isinstance(modalities, str) else list(modalities)
    bad = [item for item in modalities if item not in MODALITIES]
    if bad:
        raise ValueError(f"unknown modality {bad}; known: {MODALITIES}")
    sensitivity = str(raw.get("sensitivity") or "internal")
    if sensitivity not in SENSITIVITY:
        raise ValueError(f"sensitivity must be one of {SENSITIVITY}")
    sizes = {key: _positive((raw.get("size") or {}).get(key), f"size.{key}") for key in SIZE_KEYS}
    resources = {key: _positive((raw.get("resources") or {}).get(key), f"resources.{key}") for key in RESOURCE_KEYS}
    budget_raw = raw.get("budget") or {}
    budget = {
        "project_usd": _positive(budget_raw.get("project_usd"), "budget.project_usd"),
        "job_hard_cap_usd": _positive(budget_raw.get("job_hard_cap_usd"), "budget.job_hard_cap_usd"),
        "approved": budget_raw.get("approved") is True,
    }
    if kind in TRAINING_TYPES and not sizes["dataset_tokens"]:
        raise ValueError("training workloads need size.dataset_tokens for a quote")
    capabilities = sorted({str(item) for item in raw.get("capabilities") or []})
    workload = {
        "schema": SCHEMA,
        "type": kind,
        "modalities": modalities,
        "capabilities": capabilities,
        "unrecognized_capabilities": [item for item in capabilities if item not in KNOWN_CAPABILITIES],
        "quality_floor": _positive(raw.get("quality_floor"), "quality_floor"),
        "sensitivity": sensitivity,
        "size": {key: value for key, value in sizes.items() if value is not None},
        "resources": {key: value for key, value in resources.items() if value is not None},
        "latency": {key: _positive((raw.get("latency") or {}).get(key), f"latency.{key}") for key in ("p95_seconds", "deadline_hours")},
        "artifacts": list(raw.get("artifacts") or []),
        "license_restrictions": list(raw.get("license_restrictions") or []),
        "budget": budget,
        "reliability": {"threshold": _positive((raw.get("reliability") or {}).get("threshold"), "reliability.threshold"),
                        "independent_verification": bool((raw.get("reliability") or {}).get("independent_verification"))},
        "requirements": normalize_requirements(raw.get("requirements")),
    }
    return workload


def to_requirements(workload: dict[str, Any]) -> dict[str, Any]:
    """Router requirements implied by the workload: modalities, the
    sensitivity deployment floor, and any explicit requirements -- intersected,
    so explicit requirements can only narrow the sensitivity mapping."""
    requirements = dict(workload.get("requirements") or {})
    requirements["modalities"] = sorted(set(requirements.get("modalities") or []) | set(workload["modalities"]))
    floor = SENSITIVITY_DEPLOYMENTS.get(workload["sensitivity"])
    if floor:
        explicit = requirements.get("deployment")
        allowed = [item for item in floor if not explicit or item in explicit]
        if not allowed:
            raise ValueError(f"explicit deployment {explicit} conflicts with sensitivity {workload['sensitivity']} (allowed: {floor})")
        requirements["deployment"] = allowed
    return normalize_requirements(requirements)
