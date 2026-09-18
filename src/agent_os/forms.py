from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from .paths import ROOT
from .privacy import privacy_findings
from .storage import load_json, write_json


SANITIZER_VERSION = "1.0"
FORM_REGISTRY = ROOT / "forms" / "registry.json"
DEFAULT_QUEUE = ROOT / ".agent-local" / "form-intake" / "pending"
_GOOGLE = re.compile(r"(?:google(?:apis)?\.com|googleusercontent\.com|drive\.google\.com|docs\.google\.com|gmail\.com|firebase)", re.I)
_FORBIDDEN_KEYS = {
    "answers", "completed_values", "field_values", "ocr_text", "raw_text", "signature_image",
    "source_bytes", "source_document", "source_text", "person_name", "employee_name",
    "applicant_name", "email", "phone", "ssn", "address", "dob", "date_of_birth",
    "salary", "account_number",
}


def _clean_label(label: str) -> str:
    value = " ".join(str(label).strip().split())
    for delimiter in (":", " = ", "\t"):
        if delimiter in value:
            value = value.split(delimiter, 1)[0].strip()
    if not value or len(value) > 100:
        raise ValueError("invalid form label")
    findings = privacy_findings(value)
    if findings:
        raise ValueError(f"unsafe form label: {', '.join(findings)}")
    return value


def _signature(fingerprint: dict[str, Any]) -> str:
    labels = sorted({
        re.sub(r"\s+", " ", value.strip().casefold())
        for key in ("title_tokens", "section_labels", "field_labels")
        for value in fingerprint.get(key, [])
        if value and value.strip()
    })
    return hashlib.sha256("\n".join(labels).encode("utf-8")).hexdigest()


def _forbidden_structure(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).casefold() in _FORBIDDEN_KEYS or _forbidden_structure(nested) for key, nested in value.items())
    if isinstance(value, list):
        return any(_forbidden_structure(item) for item in value)
    return False


def sanitize_form_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    safe = deepcopy(candidate)
    allowed = {"schema", "candidate_id", "source_agent", "classification", "form", "fingerprint", "match", "candidate_action", "privacy"}
    if set(safe) - allowed:
        raise ValueError("unexpected form candidate fields")
    if _forbidden_structure(safe):
        raise ValueError("form candidate rejected by privacy gate: raw or completed values")
    fingerprint = safe.setdefault("fingerprint", {})
    for key in ("title_tokens", "section_labels", "field_labels"):
        fingerprint[key] = [_clean_label(item) for item in fingerprint.get(key, [])]
    page_count = fingerprint.get("page_count")
    if not isinstance(page_count, int) or not 1 <= page_count <= 500:
        raise ValueError("form fingerprint page_count must be between 1 and 500")
    fingerprint["version"] = 1
    fingerprint["signature"] = {"label_sha256": _signature(fingerprint)}
    safe["schema"] = "personal-agent/form-intake/v1"
    safe.setdefault("candidate_id", f"fic_{fingerprint['signature']['label_sha256'][:16]}")
    if not re.fullmatch(r"fic_[0-9a-f]{16}", safe["candidate_id"]):
        raise ValueError("invalid form candidate id")
    if safe.get("source_agent") not in {"chatgpt", "codex", "claude", "other"}:
        raise ValueError("invalid form source agent")
    safe["privacy"] = {
        "source_document_stored": False,
        "completed_values_stored": False,
        "raw_text_stored": False,
        "google_used": False,
        "sanitizer_version": SANITIZER_VERSION,
    }
    if _GOOGLE.search(str(safe)):
        raise ValueError("form candidate rejected by privacy gate: Google endpoint")
    findings = privacy_findings(safe)
    if findings:
        raise ValueError(f"form candidate rejected by privacy gate: {', '.join(findings)}")
    return safe


def score_fingerprint(fingerprint: dict[str, Any], entry: dict[str, Any]) -> float:
    labels = {
        str(item).strip().casefold()
        for key in ("title_tokens", "section_labels", "field_labels")
        for item in fingerprint.get(key, [])
        if str(item).strip()
    }
    anchors = {str(item).strip().casefold() for item in entry.get("anchors", []) if str(item).strip()}
    if not anchors:
        return 0.0
    overlap = len(labels & anchors) / len(anchors)
    page_range = entry.get("page_count_range", [1, 500])
    page_score = 1.0 if page_range[0] <= fingerprint.get("page_count", 0) <= page_range[1] else 0.0
    signature = fingerprint.get("signature", {}).get("label_sha256")
    signature_score = 1.0 if signature and signature == entry.get("signature") else 0.0
    return round(0.65 * overlap + 0.15 * page_score + 0.20 * signature_score, 4)


def best_form_match(fingerprint: dict[str, Any], registry: dict[str, Any] | None = None) -> tuple[float, dict[str, Any] | None]:
    registry = registry or load_json(FORM_REGISTRY)
    scored = [(score_fingerprint(fingerprint, entry), entry) for entry in registry.get("forms", [])]
    return max(scored, default=(0.0, None), key=lambda item: item[0])


def route_form(candidate: dict[str, Any], persist: bool = False, queue_dir: str | None = None) -> dict[str, Any]:
    classification = candidate.get("classification", {})
    if classification.get("work_related") is not True or classification.get("form_document") is not True:
        return {"classification": "not_work_form", "persisted": False}
    safe = sanitize_form_candidate(candidate)
    score, match = best_form_match(safe["fingerprint"])
    if match and score >= 0.95:
        return {"classification": "known", "score": score, "form_id": match["id"], "skill_path": match["skill_path"], "persisted": False}
    safe["match"] = {"known_form_id": match["id"] if match else None, "similarity": score}
    safe["candidate_action"] = "new_variant" if match and score >= 0.80 else "new_form"
    path = enqueue_form_candidate(safe, queue_dir) if persist else None
    return {"classification": "candidate", "score": score, "candidate": safe, "persisted": bool(path), "path": str(path) if path else None}


def enqueue_form_candidate(candidate: dict[str, Any], queue_dir: str | None = None) -> Path:
    safe = sanitize_form_candidate(candidate)
    directory = Path(queue_dir) if queue_dir else DEFAULT_QUEUE
    path = directory / f"{safe['candidate_id']}.json"
    write_json(path, safe)
    return path


def form_issue_payload(candidate: dict[str, Any]) -> dict[str, str]:
    safe = sanitize_form_candidate(candidate)
    return {
        "title": f"[FORM-INTAKE] {safe['form']['family']} / {safe['candidate_id']}",
        "body": "Sanitized form-template observation. Do not attach source documents or personal data.\n\n```form-intake-json\n" + json.dumps(safe, indent=2, ensure_ascii=False) + "\n```\n",
    }
