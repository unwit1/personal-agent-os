"""Open-source prior-art registry: lookup, staleness, task-specific discovery
queries and deterministic metadata refresh (no model call).

    agent-os orchestrate prior-art lookup "retry backoff circuit breaker"
    agent-os orchestrate prior-art queries "durable checkpoint resume for agent runs"
    agent-os orchestrate prior-art stale
    agent-os orchestrate prior-art refresh PA-inspect-ai [...] [--write]

Workflow and rules: projects/personal-agent-os/research/prior-art/README.md.
The registry informs design decisions; it never authorizes a dependency.
ADOPT/WRAP/BORROW become code only through the normal IMP -> HYP -> EXP -> EVR
-> DEC chain.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from ..paths import ROOT

REGISTRY = ROOT / "projects" / "personal-agent-os" / "research" / "prior-art" / "registry.json"
DECISIONS = {"ADOPT", "WRAP", "BORROW", "REJECT", "DEFER", "INVESTIGATE"}
REQUIRED = ("id", "name", "repository", "license", "evaluated_at", "capability_areas", "agent_os_overlap", "decision", "rationale", "confidence", "evidence", "revisit_when")
EVIDENCE_DIMENSIONS = ("development_savings", "runtime_savings", "quality", "reliability", "security", "complexity", "maintenance", "portability")
STALE_AFTER_DAYS = {"INVESTIGATE": 30, "DEFER": 120, "ADOPT": 180, "WRAP": 180, "BORROW": 365, "REJECT": 365}
_WORD = re.compile(r"[a-z0-9]+")
STOP = {"the", "a", "an", "for", "of", "and", "or", "to", "in", "on", "with", "agent", "agents", "os", "open", "source", "llm", "using", "we", "our", "is"}


def load(path: Path | None = None) -> dict[str, Any]:
    return json.loads(Path(path or REGISTRY).read_text(encoding="utf-8"))


def entry_problems(entry: Any) -> list[str]:
    if not isinstance(entry, dict):
        return ["entry is not an object"]
    label = entry.get("id", "<no id>")
    problems = [f"{label}: missing {key}" for key in REQUIRED if key not in entry]
    if not re.match(r"^PA-[a-z0-9-]+$", str(entry.get("id", ""))):
        problems.append(f"{label}: id must look like PA-<slug>")
    if entry.get("decision") not in DECISIONS:
        problems.append(f"{label}: decision must be one of {sorted(DECISIONS)}")
    if entry.get("confidence") not in {"low", "medium", "high"}:
        problems.append(f"{label}: confidence must be low/medium/high")
    evidence = entry.get("evidence")
    if isinstance(evidence, dict):
        missing = [key for key in EVIDENCE_DIMENSIONS if key not in evidence]
        if missing:
            problems.append(f"{label}: evidence missing dimensions {', '.join(missing)}")
        if "score" in evidence or "overall" in evidence:
            problems.append(f"{label}: no blended score; keep dimensions separate")
    if entry.get("decision") == "ADOPT" and not any(str(link.get("ref", "")).startswith(("EVR-", "EXP-", "DEC-")) for link in entry.get("links") or []):
        problems.append(f"{label}: ADOPT requires a linked EVR/EXP/DEC (research alone never promotes a dependency)")
    return problems


def validate(path: Path | None = None) -> list[str]:
    try:
        registry = load(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"prior-art registry: {exc}"]
    problems: list[str] = []
    seen: set[str] = set()
    for entry in registry.get("entries") or []:
        problems += entry_problems(entry)
        if isinstance(entry, dict):
            if entry.get("id") in seen:
                problems.append(f"{entry.get('id')}: duplicate id")
            seen.add(entry.get("id"))
    return problems


def _terms(text: str) -> set[str]:
    return {word for word in _WORD.findall(text.lower()) if word not in STOP and len(word) > 2}


def lookup(problem: str, registry: dict[str, Any] | None = None, limit: int = 8) -> list[dict[str, Any]]:
    """Entries relevant to a capability gap, ranked by term overlap with their
    capability areas, overlap note, useful parts and rationale."""
    registry = registry or load()
    wanted = _terms(problem)
    ranked = []
    for entry in registry.get("entries") or []:
        areas = " ".join(entry.get("capability_areas") or [])
        text = " ".join([areas, areas, entry.get("name", ""), entry.get("description", ""), entry.get("agent_os_overlap", ""), json.dumps(entry.get("useful_parts") or {}), entry.get("rationale", "")])
        hits = wanted & _terms(text)
        if hits:
            ranked.append((len(hits), entry["id"], {key: entry.get(key) for key in ("id", "name", "decision", "confidence", "capability_areas", "rationale", "evaluated_at")} | {"matched": sorted(hits)}))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked[:limit]]


def stale(registry: dict[str, Any] | None = None, today: date | None = None) -> list[dict[str, str]]:
    """Entries due for re-evaluation by age (per decision) or explicit date.
    Event triggers (release, CVE, license change, repeated local failure) are
    listed in each entry's revisit_when and checked by the agent that meets them."""
    registry = registry or load()
    today = today or date.today()
    due = []
    for entry in registry.get("entries") or []:
        try:
            evaluated = datetime.fromisoformat(str(entry.get("evaluated_at"))[:10]).date()
        except ValueError:
            due.append({"id": entry.get("id", "?"), "reason": "no valid evaluated_at"})
            continue
        limit = evaluated + timedelta(days=STALE_AFTER_DAYS.get(entry.get("decision"), 180))
        explicit = entry.get("revisit_by")
        if explicit and str(explicit)[:10] <= today.isoformat():
            due.append({"id": entry["id"], "reason": f"revisit_by {explicit}"})
        elif today >= limit:
            due.append({"id": entry["id"], "reason": f"{entry.get('decision')} older than {STALE_AFTER_DAYS.get(entry.get('decision'), 180)} days"})
    return due


def queries(problem: str, registry: dict[str, Any] | None = None) -> list[str]:
    """Task-specific discovery queries derived from the capability gap, never a
    generic 'best agent framework' search. Adds the gap's own key terms, the
    capability areas of related entries, and 'alternative to <known project>'."""
    registry = registry or load()
    core = " ".join(sorted(_terms(problem), key=problem.lower().find)[:6])
    related = lookup(problem, registry, limit=3)
    out = [f"open source {core} github", f"{core} python library", f"{core} benchmark repository", f"{core} paper code"]
    for entry in related:
        out.append(f"alternative to {entry['name']} {' '.join((entry.get('capability_areas') or [])[:2])}")
    out.append(f"{core} site:github.com")
    return list(dict.fromkeys(out))


def github_facts(repository: str, opener=None) -> dict[str, Any]:
    """Deterministic repository facts from the public GitHub REST API."""
    match = re.search(r"github\.com/([^/]+/[^/#?]+)", repository)
    if not match:
        return {"ok": False, "error": "not a GitHub repository"}
    slug = match.group(1).removesuffix(".git")
    fetch = opener or urllib.request.urlopen

    def get(url: str) -> dict[str, Any]:
        request = urllib.request.Request(url, headers={"User-Agent": "agent-os-prior-art/1", "Accept": "application/vnd.github+json"})
        with fetch(request, timeout=20) as response:
            return json.loads(response.read().decode())

    try:
        meta = get(f"https://api.github.com/repos/{slug}")
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}
    try:
        release = get(f"https://api.github.com/repos/{slug}/releases/latest")
        latest, released = release.get("tag_name"), str(release.get("published_at") or "")[:10] or None
    except Exception:
        latest, released = None, None
    return {"ok": True, "license": (meta.get("license") or {}).get("spdx_id"), "stars": meta.get("stargazers_count"), "pushed_at": str(meta.get("pushed_at") or "")[:10],
            "archived": bool(meta.get("archived")), "language": meta.get("language"), "latest_release": latest, "released_at": released}


def refresh(ids: list[str], *, write: bool = False, path: Path | None = None, opener=None) -> list[dict[str, Any]]:
    """Update activity facts for the given entries (or all when empty). Records
    what changed so an agent can decide whether a revisit trigger fired."""
    target = Path(path or REGISTRY)
    registry = load(target)
    changes = []
    for entry in registry.get("entries") or []:
        if ids and entry["id"] not in ids:
            continue
        facts = github_facts(entry.get("repository", ""), opener)
        if not facts.get("ok"):
            changes.append({"id": entry["id"], "error": facts.get("error")})
            continue
        before = entry.get("activity") or {}
        activity = {key: facts[key] for key in ("stars", "pushed_at", "archived", "latest_release", "released_at")}
        diff = {key: [before.get(key), value] for key, value in activity.items() if before.get(key) != value and key != "stars"}
        if facts.get("license") and facts["license"] != entry.get("license_spdx"):
            diff["license_spdx"] = [entry.get("license_spdx"), facts["license"]]
            entry["license_spdx"] = facts["license"]
        entry["activity"] = {**before, **activity, "checked_at": date.today().isoformat()}
        changes.append({"id": entry["id"], "changed": diff})
    if write:
        target.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return changes
