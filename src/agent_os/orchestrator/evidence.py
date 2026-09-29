"""Orchestrator OS durable state: typed evidence records, eval suites, the
external corpus registry, status manifest and checkpoints -- validated
deterministically by ``agent-os validate`` (see validation.py).

Records live in Git under projects/personal-agent-os/orchestrator-os/ and
follow schemas/evidence-record-v1.schema.json. Links must resolve: a ``ref``
is a record id that exists (evidence records, IMP-*, MIE-* research backlog
items), an existing repository path, ``commit:<sha>``, ``local:<ref>`` (a
machine-local reference that is intentionally not in Git), or ``url:``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..paths import ROOT

OS_DIR = ROOT / "projects" / "personal-agent-os" / "orchestrator-os"
RESEARCH_BACKLOG = ROOT / "projects" / "personal-agent-os" / "research" / "meta-improvement" / "improvement-backlog.json"
IMPROVEMENTS = ROOT / "projects" / "personal-agent-os" / "improvements"
POLICY = ROOT / "policy" / "orchestrator-os.policy.json"
TYPES = {"OBS", "CLM", "FND", "FAIL", "SUC", "HYP", "EXP", "EVC", "EVS", "EVR", "DEC", "REL", "CAP", "RAD", "Q"}
STATUSES = {"active", "open", "proposed", "accepted", "rejected", "inconclusive", "superseded", "resolved", "promoted", "rolled_back", "draft"}
RELS = {"evidence_for", "evidence_against", "derived_from", "tests", "measures", "decides", "implements", "supersedes", "blocks", "answers", "relates_to", "rolls_back", "baseline", "candidate"}
_ID = re.compile(r"^(OBS|CLM|FND|FAIL|SUC|HYP|EXP|EVC|EVS|EVR|DEC|REL|CAP|RAD|Q)-[0-9A-Za-z-]{4,}$")
_EXTERNAL_ID = re.compile(r"^(IMP|MIE|ORCH|XC)-[0-9A-Za-z-]+$")
PERMISSIONS = {"yes", "no", "unverified"}
STATUS_KEYS = {"schema", "phase", "active_objective", "next_action", "completed", "blockers", "recent_decisions"}


def _load(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")
        return None


def records(root: Path | None = None) -> list[tuple[Path, dict[str, Any]]]:
    found = []
    for path in sorted(Path(root or OS_DIR / "records").rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        found.append((path, data))
    return found


def known_external_ids() -> set[str]:
    ids: set[str] = set()
    try:
        ids |= {item["id"] for item in json.loads(RESEARCH_BACKLOG.read_text(encoding="utf-8"))["items"]}
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        pass
    ids |= {path.stem for path in IMPROVEMENTS.glob("IMP-*.json")}
    ids |= {path.stem for path in (OS_DIR / "checkpoints").glob("ORCH-*.json")}
    return ids


def validate_record(data: Any, label: str) -> list[str]:
    if not isinstance(data, dict):
        return [f"{label}: not a JSON object"]
    errors = []
    missing = sorted({"schema", "id", "type", "title", "status"} - data.keys())
    if missing:
        errors.append(f"{label}: missing {', '.join(missing)}")
    if data.get("schema") != "personal-agent/evidence-record/v1":
        errors.append(f"{label}: schema must be personal-agent/evidence-record/v1")
    if not _ID.match(str(data.get("id", ""))):
        errors.append(f"{label}: invalid id {data.get('id')!r}")
    elif data.get("type") != str(data["id"]).split("-")[0]:
        errors.append(f"{label}: id prefix does not match type {data.get('type')!r}")
    if data.get("type") not in TYPES:
        errors.append(f"{label}: unknown type {data.get('type')!r}")
    if data.get("status") not in STATUSES:
        errors.append(f"{label}: unknown status {data.get('status')!r}")
    if data.get("type") != "CAP" and not data.get("created_at"):
        errors.append(f"{label}: missing created_at")
    for link in data.get("links") or []:
        if not isinstance(link, dict) or link.get("rel") not in RELS or not link.get("ref"):
            errors.append(f"{label}: malformed link {link!r}")
    return errors


def _ref_ok(ref: str, ids: set[str]) -> bool:
    if ref.startswith(("local:", "url:", "commit:", "research:")):
        return True
    if ref in ids:
        return True
    path = ref.split("#")[0].split(":")[0]
    return bool(path) and (ROOT / path).exists()


def validate_tree() -> dict[str, Any]:
    """All Orchestrator OS state. Returns {errors, warnings, checked}."""
    errors: list[str] = []
    warnings: list[str] = []
    checked = 0
    if not OS_DIR.exists():
        return {"errors": [], "warnings": ["orchestrator-os state directory absent"], "checked": 0}

    policy = _load(POLICY, errors)
    checked += 1
    if isinstance(policy, dict):
        for key in ("principles", "execution_hierarchy", "control_plane", "promotion", "stop_conditions", "routing", "budgets"):
            if key not in policy:
                errors.append(f"policy/orchestrator-os.policy.json: missing {key}")
        for pattern in (policy.get("control_plane") or {}).get("protected_paths") or []:
            if not pattern.endswith("/**") and "*" not in pattern and not (ROOT / pattern).exists():
                warnings.append(f"protected path does not exist yet: {pattern}")

    all_records = records()
    ids = known_external_ids() | {data["id"] for _, data in all_records if isinstance(data, dict) and data.get("id")}
    seen: set[str] = set()
    for path, data in all_records:
        checked += 1
        label = path.relative_to(ROOT).as_posix()
        problems = validate_record(data, label)
        errors.extend(problems)
        if problems:
            continue
        if data["id"] in seen:
            errors.append(f"{label}: duplicate record id {data['id']}")
        seen.add(data["id"])
        if path.stem != data["id"]:
            errors.append(f"{label}: file name must equal record id")
        for link in data.get("links") or []:
            if not _ref_ok(str(link["ref"]), ids):
                errors.append(f"{label}: unresolved link {link['rel']} -> {link['ref']}")

    for path in sorted((OS_DIR / "evals" / "suites").glob("*.json")):
        checked += 1
        suite = _load(path, errors)
        if isinstance(suite, dict):
            problems = validate_record(suite, path.relative_to(ROOT).as_posix())
            errors.extend(problems)
            if not problems and suite["type"] != "EVS":
                errors.append(f"{path.name}: suites must be EVS records")
            for runner in (suite.get("metrics") or {}).get("runners") or []:
                target = str(runner).split("::")[0]
                if not (ROOT / target).exists():
                    errors.append(f"{path.name}: runner target missing: {target}")

    corpora_path = OS_DIR / "evals" / "external-corpora.json"
    if corpora_path.exists():
        corpora = _load(corpora_path, errors) or {}
        for entry in corpora.get("corpora") or []:
            checked += 1
            label = f"external corpus {entry.get('id')}"
            missing = sorted({"id", "name", "source", "license", "permissions", "holdout_state", "contamination_risk", "task_families", "status"} - entry.keys())
            if missing:
                errors.append(f"{label}: missing {', '.join(missing)}")
                continue
            if any(entry["permissions"].get(key) not in PERMISSIONS for key in ("training", "fine_tune", "evaluation", "redistribution")):
                errors.append(f"{label}: permissions must be yes/no/unverified")
            if entry["status"] == "imported" and entry["permissions"].get("evaluation") != "yes":
                errors.append(f"{label}: imported without verified evaluation permission")
            if entry["holdout_state"] == "protected_holdout" and entry["permissions"].get("training") == "yes" and entry.get("used_for_training"):
                errors.append(f"{label}: protected holdout also used for training")

    from .prior_art import REGISTRY as PRIOR_ART, validate as prior_art_problems

    if PRIOR_ART.exists():
        checked += 1
        errors.extend(f"prior-art: {item}" for item in prior_art_problems())
    for path, data in all_records:
        # From DEC-0008 on, decisions state what prior art was checked.
        if isinstance(data, dict) and data.get("type") == "DEC" and re.match(r"^DEC-(\d+)$", str(data.get("id"))) and int(str(data["id"])[4:]) >= 8 and "prior_art" not in data:
            warnings.append(f"{data['id']}: no prior_art note (see projects/personal-agent-os/research/prior-art/README.md)")

    status_path = OS_DIR / "status.json"
    status = _load(status_path, errors) if status_path.exists() else None
    if status is None:
        errors.append("orchestrator-os/status.json missing")
    else:
        checked += 1
        missing = sorted(STATUS_KEYS - status.keys())
        if missing:
            errors.append(f"orchestrator-os/status.json: missing {', '.join(missing)}")
        for ref in (status.get("next_action") or {}).get("context_refs") or []:
            if not _ref_ok(str(ref), ids):
                errors.append(f"orchestrator-os/status.json: unresolved context ref {ref}")

    for path in sorted((OS_DIR / "checkpoints").glob("ORCH-*.json")):
        checked += 1
        checkpoint = _load(path, errors)
        if isinstance(checkpoint, dict):
            missing = sorted({"schema", "id", "created_at", "git", "phase", "active_objective", "next_action", "next_prompt"} - checkpoint.keys())
            if missing:
                errors.append(f"{path.name}: missing {', '.join(missing)}")
            elif checkpoint["id"] != path.stem:
                errors.append(f"{path.name}: id mismatch")
    return {"errors": errors, "warnings": warnings, "checked": checked}
