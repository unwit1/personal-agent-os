"""External benchmark corpus registry and importers (MIE-0019 / EVS-SECURITY).

Third-party attack corpora are imported *as data*, never authored here
(FND-0013). Nothing is fetched until an operator runs an import, licenses and
permissions are verified against the source before use, and the fetched
content lives only under ``.agent-local/corpora/`` (gitignored) -- Git keeps
the registry entry, counts and provenance, never the payloads.

    agent-os orchestrate corpus list
    agent-os orchestrate corpus import XC-agentdojo [--write]

The registry entries follow ``schemas/external-corpus-v1.schema.json`` and
live in ``projects/personal-agent-os/orchestrator-os/evals/external-corpora.json``.
"""

from __future__ import annotations

import ast
import json
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Callable

from ..paths import ROOT

REGISTRY = ROOT / "projects" / "personal-agent-os" / "orchestrator-os" / "evals" / "external-corpora.json"
LOCAL_ROOT = ROOT / ".agent-local" / "corpora"
RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"

# AgentDojo (ethz-spylab/agentdojo, MIT), pinned. Injection-task modules hold
# BaseInjectionTask subclasses whose GOAL string is the attacker objective.
AGENTDOJO = {
    "id": "XC-agentdojo",
    "repo": "ethz-spylab/agentdojo",
    "ref": "089ed468cf3e",
    "paths": [
        "src/agentdojo/default_suites/v1/banking/injection_tasks.py",
        "src/agentdojo/default_suites/v1/slack/injection_tasks.py",
        "src/agentdojo/default_suites/v1/travel/injection_tasks.py",
        "src/agentdojo/default_suites/v1/workspace/injection_tasks.py",
    ],
}


def load_registry(path: Path | None = None) -> dict[str, Any]:
    return json.loads(Path(path or REGISTRY).read_text(encoding="utf-8"))


def _fetch(url: str, opener: Callable[..., Any] | None = None) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "agent-os-corpus/1"})
    with (opener or urllib.request.urlopen)(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def parse_injection_tasks(source: str) -> list[dict[str, Any]]:
    """(class name, GOAL, difficulty) for each BaseInjectionTask subclass in a
    module. Reads the GOAL string literal statically; runs no fetched code."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    tasks = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not any("InjectionTask" in getattr(base, "id", getattr(base, "attr", "")) for base in node.bases):
            continue
        goal, difficulty = None, None

        def _text(value: ast.AST | None) -> str | None:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return value.value
            if isinstance(value, ast.JoinedStr):  # f-string: keep literals, mark {expr}
                return ast.unparse(value)
            return None

        for stmt in node.body:
            target = None
            value = None
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                target, value = stmt.target.id, stmt.value
            elif isinstance(stmt, ast.Assign) and stmt.targets and isinstance(stmt.targets[0], ast.Name):
                target, value = stmt.targets[0].id, stmt.value
            if target == "GOAL":
                goal = _text(value)
            elif target == "DIFFICULTY" and value is not None:
                difficulty = ast.unparse(value)
        if goal is not None:
            tasks.append({"task": node.name, "goal": goal, "difficulty": difficulty})
    return tasks


def import_agentdojo(*, write: bool = False, opener: Callable[..., Any] | None = None, local_root: Path | None = None, spec: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fetch AgentDojo injection-task modules at the pinned revision and store
    a machine-local index of attacker goals (gitignored). Returns a summary;
    the goals themselves are never returned or committed."""
    spec = spec or AGENTDOJO
    local = Path(local_root or LOCAL_ROOT) / "agentdojo"
    suites = []
    total = 0
    for path in spec["paths"]:
        suite = path.split("/")[-2]
        try:
            source = _fetch(RAW.format(repo=spec["repo"], ref=spec["ref"], path=path), opener)
        except Exception as exc:  # network or 404
            return {"id": spec["id"], "ok": False, "error": f"{type(exc).__name__}: {exc}"[:160], "fetched": len(suites)}
        tasks = parse_injection_tasks(source)
        total += len(tasks)
        suites.append({"suite": suite, "path": path, "tasks": len(tasks)})
        if write:
            local.mkdir(parents=True, exist_ok=True)
            (local / f"{suite}.json").write_text(json.dumps({"suite": suite, "source": path, "ref": spec["ref"], "tasks": tasks}, indent=1), encoding="utf-8")
    local_ref = (local.relative_to(ROOT).as_posix() if local.is_relative_to(ROOT) else str(local)) if write else None
    summary = {"id": spec["id"], "ok": True, "repo": spec["repo"], "ref": spec["ref"], "suites": suites, "injection_tasks": total,
               "local_ref": local_ref, "imported_at": date.today().isoformat() if write else None, "committed": False}
    if write:
        (local / "index.json").write_text(json.dumps({k: v for k, v in summary.items() if k != "committed"}, indent=1), encoding="utf-8")
    return summary


def apply_import_to_registry(summary: dict[str, Any], path: Path | None = None) -> None:
    """Update the registry entry with the import outcome (counts, local_ref,
    imported_at). Never writes payloads into the registry."""
    target = Path(path or REGISTRY)
    registry = load_registry(target)
    for entry in registry.get("corpora", []):
        if entry.get("id") == summary["id"]:
            entry["revision"] = summary["ref"]
            entry["local_ref"] = summary.get("local_ref")
            entry["imported_at"] = summary.get("imported_at")
            entry["derived_cases"] = [f"{s['suite']}:{s['tasks']} injection tasks" for s in summary.get("suites", [])]
            entry["status"] = "imported" if summary.get("ok") and summary.get("local_ref") else entry.get("status", "candidate")
    target.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8", newline="\n")
