from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .adapters import ADAPTER
from .candidates import KINDS, STATUSES
from .changes import CHANGE_TYPES, STATUSES as CHANGE_STATUSES
from .documents import CACHE_DIR
from .improvements import CATEGORIES, PRIORITIES, STATUSES as IMPROVEMENT_STATUSES
from .paths import ROOT
from .privacy import privacy_findings
from .profile import CANONICAL_SOURCES, index_facts, retrievable_facts
from .registry import load_state, projects
from .routing import status as routing_status
from .skills import discover
from .surfaces import SURFACE_REGISTRY_PATH, SURFACE_REGISTRY_SCHEMA, TIERS, surfaces
from .storage import load_json
from .workflows import FORBIDDEN_RUN_KEYS, WORKFLOW_DIR, manifest_problems, ordered_stage_ids


SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "generic api key": re.compile(r"(?i)(?:api[_-]?key|secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}"),
}


def _required(data: dict[str, Any], keys: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(keys - data.keys())
    if missing:
        errors.append(f"{label}: missing {', '.join(missing)}")


def validate() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    checked = 0

    try:
        known_projects = projects()
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        return {"ok": False, "errors": [f"project registry: {exc}"], "warnings": [], "checked": 0}

    ids: set[str] = set()
    for project in known_projects:
        checked += 1
        _required(project, {"id", "name", "path", "state_file"}, "project", errors)
        project_id = project.get("id", "")
        if project_id in ids:
            errors.append(f"duplicate project id: {project_id}")
        ids.add(project_id)
        if project.get("redirect_to") and project["redirect_to"] not in {item.get("id") for item in known_projects}:
            errors.append(f"{project_id}: unknown redirect target {project['redirect_to']}")
        state_path = ROOT / project.get("state_file", "")
        if not state_path.exists():
            errors.append(f"missing project state: {state_path}")
            continue
        state = load_state(project)
        _required(state, {"schema_version", "project", "status", "summary", "context_files", "validation_commands"}, project_id, errors)
        if state.get("project") != project_id:
            errors.append(f"{project_id}: state project id mismatch")
        project_path = Path(project["path"])
        if not project_path.exists():
            warnings.append(f"{project_id}: local checkout not found at {project_path}")
        else:
            for relative in state.get("context_files", []):
                candidate = (project_path / relative).resolve()
                try:
                    candidate.relative_to(project_path.resolve())
                except ValueError:
                    errors.append(f"{project_id}: context path escapes project: {relative}")
                    continue
                if not candidate.exists():
                    errors.append(f"{project_id}: missing context file: {relative}")
            project_skills = discover(project_path, state.get("skill_roots", []))
            skill_names: set[str] = set()
            for skill in project_skills:
                checked += 1
                if not skill.description:
                    errors.append(f"skill has no discoverable description: {skill.path}")
                if skill.name in skill_names:
                    errors.append(f"{project_id}: duplicate skill name: {skill.name}")
                skill_names.add(skill.name)

    for skill in discover():
        checked += 1
        if not skill.description:
            errors.append(f"skill has no description: {skill.path}")

    for handoff_path in sorted((ROOT / "projects").glob("*/handoffs/*.json")):
        checked += 1
        try:
            handoff = load_json(handoff_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid handoff {handoff_path}: {exc}")
            continue
        _required(
            handoff,
            {"schema_version", "project", "created_at", "completed", "remaining", "validation"},
            str(handoff_path.relative_to(ROOT)),
            errors,
        )

    for candidate_path in sorted((ROOT / "projects").glob("*/candidates/*.json")):
        checked += 1
        try:
            candidate = load_json(candidate_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid candidate {candidate_path}: {exc}")
            continue
        _required(candidate, {"id", "kind", "statement", "status", "created_at"}, str(candidate_path.relative_to(ROOT)), errors)
        if candidate.get("kind") not in KINDS:
            errors.append(f"{candidate_path.relative_to(ROOT)}: unsupported candidate kind")
        if candidate.get("status") not in STATUSES:
            errors.append(f"{candidate_path.relative_to(ROOT)}: unsupported candidate status")

    for improvement_path in sorted((ROOT / "projects").glob("*/improvements/IMP-*.json")):
        checked += 1
        try:
            improvement = load_json(improvement_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid improvement {improvement_path}: {exc}")
            continue
        _required(improvement, {"schema_version", "id", "project", "title", "category", "status", "priority", "observation", "suggested_direction", "acceptance", "created_at", "updated_at"}, str(improvement_path.relative_to(ROOT)), errors)
        if improvement.get("category") not in CATEGORIES:
            errors.append(f"{improvement_path.relative_to(ROOT)}: unsupported improvement category")
        if improvement.get("status") not in IMPROVEMENT_STATUSES:
            errors.append(f"{improvement_path.relative_to(ROOT)}: unsupported improvement status")
        if improvement.get("priority") not in PRIORITIES:
            errors.append(f"{improvement_path.relative_to(ROOT)}: unsupported improvement priority")
        findings = privacy_findings(improvement)
        if findings:
            errors.append(f"{improvement_path.relative_to(ROOT)}: privacy findings {', '.join(findings)}")

    for change_path in sorted((ROOT / "projects").glob("*/changes/CR-*.json")):
        checked += 1
        try:
            change = load_json(change_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid change {change_path}: {exc}")
            continue
        _required(change, {"schema_version", "change_id", "created_at", "updated_at", "change_type", "status", "title", "request_summary", "routing", "privacy"}, str(change_path.relative_to(ROOT)), errors)
        if change.get("change_type") not in CHANGE_TYPES:
            errors.append(f"{change_path.relative_to(ROOT)}: unsupported change type")
        if change.get("status") not in CHANGE_STATUSES:
            errors.append(f"{change_path.relative_to(ROOT)}: unsupported change status")
        if change.get("privacy", {}).get("contains_raw_private_source") is not False:
            errors.append(f"{change_path.relative_to(ROOT)}: raw private source is forbidden")
        findings = privacy_findings(change)
        if findings:
            errors.append(f"{change_path.relative_to(ROOT)}: privacy findings {', '.join(findings)}")

    for source in CANONICAL_SOURCES:
        checked += 1
        if not source.exists():
            warnings.append(f"profile source is missing: {source.name}")
    try:
        profile_facts = index_facts()
    except (OSError, ValueError) as exc:
        errors.append(f"profile index: {exc}")
        profile_facts = []
    checked += 1
    if CANONICAL_SOURCES[0].exists() and not profile_facts:
        errors.append("profile sources exist but index no facts")
    for fact in retrievable_facts():
        checked += 1
        if fact["privacy_findings"]:
            errors.append(f"retrievable profile fact {fact['id']} carries {', '.join(fact['privacy_findings'])}")

    checked += 1
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    if ".agent-local/" not in gitignore:
        errors.append("the private local-runtime directory is not gitignored")
    checked += 1
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(CACHE_DIR.relative_to(ROOT))],
            cwd=str(ROOT), capture_output=True, text=True, timeout=30,
        )
        if tracked.returncode == 0 and tracked.stdout.strip():
            errors.append("the document cache is tracked in Git; it holds derived work-document text")
    except (OSError, subprocess.SubprocessError):
        pass
    form_registry = ROOT / "forms" / "registry.json"
    checked += 1
    if not form_registry.exists():
        errors.append("missing compact form registry")
    else:
        registry = load_json(form_registry)
        _required(registry, {"schema", "version", "forms"}, "form registry", errors)
        if registry.get("schema") != "personal-agent/form-registry/v1":
            errors.append("form registry: unsupported schema")

    surface_ids: set[str] = set()
    checked += 1
    if not SURFACE_REGISTRY_PATH.exists():
        errors.append("missing client surface registry")
    else:
        registry = load_json(SURFACE_REGISTRY_PATH)
        _required(registry, {"schema", "version", "surfaces"}, "surface registry", errors)
        if registry.get("schema") != SURFACE_REGISTRY_SCHEMA:
            errors.append("surface registry: unsupported schema")
        else:
            for surface in surfaces():
                checked += 1
                label = f"surface {surface.get('id', '?')}"
                _required(surface, {"id", "name", "vendor", "mechanism", "expected_tier", "summary", "invocation", "instruction", "capture"}, label, errors)
                if surface.get("id") in surface_ids:
                    errors.append(f"duplicate surface id: {surface.get('id')}")
                surface_ids.add(surface.get("id"))
                if surface.get("expected_tier") not in TIERS:
                    errors.append(f"{label}: unsupported expected tier")
                if surface.get("invocation", {}).get("kind") not in {"mcp_stdio", "server_entrypoint", "none"}:
                    errors.append(f"{label}: unsupported invocation kind")
                if surface.get("instruction", {}).get("kind") not in {"instruction_file", "bridge_document", "server_instructions", "none"}:
                    errors.append(f"{label}: unsupported instruction kind")
                if surface.get("capture", {}).get("kind") not in {"mcp_tools", "cli_bridge", "none"}:
                    errors.append(f"{label}: unsupported capture kind")
                for location in surface.get("instruction", {}).get("locations", []):
                    if str(location).casefold().startswith("repo/") and not (ROOT / str(location)[5:]).exists():
                        errors.append(f"{label}: missing bridge document {location}")
            if "claude-code" not in surface_ids:
                errors.append("surface registry: Claude Code is not a registered client surface")

    for manifest_path in sorted(WORKFLOW_DIR.glob("*.json")) if WORKFLOW_DIR.exists() else []:
        checked += 1
        label = str(manifest_path.relative_to(ROOT))
        try:
            manifest = load_json(manifest_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid workflow manifest {label}: {exc}")
            continue
        for problem in manifest_problems(manifest):
            errors.append(f"{label}: {problem}")
        if manifest_path.stem != manifest.get("workflow_id"):
            errors.append(f"{label}: filename does not match workflow_id")
        if manifest.get("project") not in ids:
            errors.append(f"{label}: unknown project {manifest.get('project')}")

    for run_path in sorted((ROOT / "projects").glob("*/workflows/*.json")):
        checked += 1
        label = str(run_path.relative_to(ROOT))
        try:
            record = load_json(run_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid workflow run {label}: {exc}")
            continue
        _required(record, {"schema_version", "run_id", "workflow_id", "project", "status", "stages"}, label, errors)
        leaked = FORBIDDEN_RUN_KEYS.intersection(record)
        if leaked:
            errors.append(f"{label}: run state carries conversation context: {', '.join(sorted(leaked))}")
        manifest_file = WORKFLOW_DIR / f"{record.get('workflow_id')}.json"
        if not manifest_file.exists():
            warnings.append(f"{label}: run references a workflow manifest that no longer exists")
            continue
        try:
            manifest = load_json(manifest_file)
        except (OSError, json.JSONDecodeError):
            continue
        if manifest_problems(manifest):
            continue
        unknown = set(record.get("stages", {})) - set(ordered_stage_ids(manifest))
        if unknown:
            errors.append(f"{label}: run records stages absent from the manifest: {', '.join(sorted(unknown))}")

    required_schemas = {"change-packet.schema.json", "google-safe-projection.schema.json", "improvement.schema.json", "form-fingerprint-v1.schema.json", "form-intake-v1.schema.json", "form-registry-v1.schema.json", "surface-registry-v1.schema.json", "workflow-manifest-v1.schema.json"}
    for schema_name in required_schemas:
        checked += 1
        if not (ROOT / "schemas" / schema_name).exists():
            errors.append(f"missing schema: {schema_name}")

    for review_path in sorted((ROOT / "reviews").glob("*.json")):
        checked += 1
        try:
            review = load_json(review_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid review {review_path}: {exc}")
            continue
        _required(review, {"task_id", "review_level", "status", "findings"}, str(review_path.relative_to(ROOT)), errors)
        if review.get("review_level") not in {0, 1, 2, 3}:
            errors.append(f"{review_path.relative_to(ROOT)}: invalid review level")

    canonical = "policy/CANONICAL_AGENT_POLICY.md"
    for adapter in (ROOT / "AGENTS.md", ROOT / "CLAUDE.md"):
        checked += 1
        text = adapter.read_text(encoding="utf-8") if adapter.exists() else ""
        if canonical not in text:
            errors.append(f"adapter does not reference canonical policy: {adapter.name}")
        if len(text) > 2000:
            warnings.append(f"adapter is larger than 2000 characters: {adapter.name}")
        if text != ADAPTER:
            errors.append(f"generated adapter is out of sync: {adapter.name}")

    excluded = {".git", ".agent-os", ".agent-local", ".tmp", ".venv", ".bootstrap_staging_v3"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        if path.suffix.casefold() not in {".md", ".json", ".py", ".toml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"possible {label}: {path.relative_to(ROOT)}")

    for item in routing_status():
        checked += 1
        if not item["exists"]:
            warnings.append(f"routing adapter is not installed: {item['destination']}")
        elif not item["matches"]:
            warnings.append(f"routing adapter differs from canonical source: {item['destination']}")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "checked": checked}
