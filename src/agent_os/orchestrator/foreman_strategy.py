"""Foreman strategy: fit the planning style to the model doing the planning.

Three questions, all answered without a model call:

1. **Which model is the operator using right now?** (``host_models``) --
   Claude Code: the newest session transcript's assistant ``model`` field,
   else ``~/.claude/settings.json``; effort from ``CLAUDE_EFFORT``. Codex:
   ``~/.codex/config.toml`` ``model`` / ``model_reasoning_effort``. Only those
   fields are read.
2. **How strong a planner is a given model?** (``strength``) -- from the best
   evidence available, most specific first, so it adapts by itself as new
   models, benchmarks and measurements appear:
   a. measured ``foreman eval`` reports for that exact model (judgement
      accuracy and plan validity on labelled planning cases);
   b. benchmark evidence (``intelligence_index`` in model_value's evidence),
      relative to the best model on record;
   c. the tier the model fills in its provider's lineup (reasoning/frontier >
      balanced > fast), or a size hint for open weights (e.g. ``14B``).
3. **What should a planner of that strength do?** (``PLAYBOOKS``) --
   ``strong``: spend its planning power on precise, small task specs and push
   work to the cheapest tier that will pass (e.g. Opus planning, Luna/Haiku
   implementing). ``medium``: the default planner rules. ``weak``: keep plans
   short, and let the deterministic ``guard`` correct its model choices
   (raise one task to ``reasoning`` for design/concurrency/security goals,
   lower trivial doc/typo tasks to ``fast``); ``consult`` recommends a
   stronger planner when one is available.

Playbooks are data: edit ``PLAYBOOKS`` or override per machine in
``~/.agent-os/foreman-playbooks.json`` (same keys) without code changes.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from ..capabilities import CAPABILITY_CLASSES, rank

BANDS = ("weak", "medium", "strong")
TIER_SCORE = {"frontier": 0.95, "reasoning": 0.85, "balanced": 0.6, "fast": 0.35}
PLAYBOOKS: dict[str, dict[str, Any]] = {
    "strong": {
        "summary": "strong planner: invest in precise specs, delegate to the cheapest tier that passes",
        "prioritize": ["decomposition into small independently verifiable tasks", "exact file/function-level instructions",
                       "choosing the cheapest capability class per task", "design decisions written to files for fast tasks to follow"],
        "planner_addendum": ("You are a strong planner and your planning is the most valuable use of this call. Write each task so a "
                             "`fast` model can finish it on the first try: name the exact file, function and expected behaviour. "
                             "Prefer more, smaller `fast` tasks; use `reasoning` only for a genuine design decision."),
        "guard": False,
        "consult": False,
    },
    "medium": {
        "summary": "capable planner: default rules",
        "prioritize": ["clear task boundaries", "sensible capability classes"],
        "planner_addendum": "",
        "guard": False,
        "consult": False,
    },
    "weak": {
        "summary": "limited planner: short plans, deterministic class guard, consult a stronger planner when one is available",
        "prioritize": ["few, concrete tasks", "copying file names from the repository map exactly", "leaving design to a reasoning task"],
        "planner_addendum": ("Keep the plan short (at most 4 tasks). Copy file paths exactly from the repository map. If the goal involves "
                             "design, concurrency, locking or security, give that part to one `reasoning` task; everything "
                             "mechanical is `fast`."),
        "guard": True,
        "consult": True,
    },
}
RISKY = re.compile(r"\b(design|architect\w*|concurren\w*|race|lock(ing|s)?|deadlock|thread\w*|security|secret\w*|auth\w*|crypt\w*|"
                   r"protocol|migration|cross-cutting|invariant|audit)\b", re.I)
TRIVIAL = re.compile(r"\b(typo|misspell\w*|spelling|docs?|readme|comment\w*|rename|format\w*|wording|changelog)\b", re.I)
_SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*[bB]\b")


# ---------------------------------------------------------------------------
# 1. Host models
# ---------------------------------------------------------------------------


def _claude_model(home: Path) -> tuple[str | None, str]:
    transcripts = sorted((home / ".claude" / "projects").glob("*/*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)[:1]
    for path in transcripts:
        try:
            with path.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                handle.seek(max(handle.tell() - 400_000, 0))
                tail = handle.read().decode("utf-8", errors="replace")
        except OSError:
            continue
        found = re.findall(r'"model"\s*:\s*"(claude-[a-z0-9.-]+)"', tail)
        if found:
            return found[-1], f"latest Claude Code session ({path.name})"
    try:
        model = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8")).get("model")
        return (str(model), "~/.claude/settings.json") if model else (None, "")
    except (OSError, ValueError):
        return None, ""


def _codex_model(home: Path) -> tuple[str | None, str | None]:
    try:
        text = (home / ".codex" / "config.toml").read_text(encoding="utf-8")
    except OSError:
        return None, None
    model = re.search(r'^\s*model\s*=\s*"([^"]+)"', text, re.M)
    effort = re.search(r'^\s*model_reasoning_effort\s*=\s*"([^"]+)"', text, re.M)
    return (model.group(1) if model else None), (effort.group(1) if effort else None)


def host_models(home: Path | None = None, environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Which models the operator's own tools are set to, and which tool is calling."""
    home = Path(home or Path.home())
    environ = dict(os.environ if environ is None else environ)
    hosts: dict[str, Any] = {}
    model, source = _claude_model(home)
    if model:
        hosts["claude"] = {"provider_hint": "claude-code", "model": model, "effort": environ.get("CLAUDE_EFFORT"), "source": source}
    model, effort = _codex_model(home)
    if model:
        hosts["chatgpt"] = {"provider_hint": "codex", "model": model, "effort": effort, "source": "~/.codex/config.toml"}
    agent = (environ.get("AI_AGENT") or "").lower()
    active = "claude" if environ.get("CLAUDECODE") == "1" or agent.startswith("claude") else "chatgpt" if agent.startswith("codex") else None
    return {"active": active, "hosts": hosts}


# ---------------------------------------------------------------------------
# 2. Strength
# ---------------------------------------------------------------------------


def _eval_reports(eval_dir: Path | None) -> list[dict[str, Any]]:
    if eval_dir is None:
        from .store import orchestrator_home

        eval_dir = orchestrator_home() / "foreman-eval"
    reports = []
    for path in sorted(Path(eval_dir).glob("*/report.json")):
        try:
            reports.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return reports


def _measured(model: str, reports: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Latest completed eval of this exact model (aborted runs say nothing about judgement)."""
    for report in reversed(reports):
        if report.get("aborted"):
            continue
        served = {str((row.get("usage") or {}).get("model_resolved") or "") for row in report.get("cases") or []}
        if model in served or report.get("model") == model:
            summary = report.get("summary") or {}
            if summary.get("cases"):
                return summary
    return None


def _tier_of(model: str, provider: dict[str, Any] | None) -> str | None:
    models = (provider or {}).get("models") or {}
    if len(set(models.values())) <= 1:
        return None  # one model behind every tier (a served endpoint): the tier says nothing
    for tier, name in models.items():
        if name == model:
            return tier
    return None


def strength(model: str, *, provider: dict[str, Any] | None = None, evidence: dict[str, Any] | None = None,
             reports: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Score 0..1 and band for ``model`` as a planner, with the evidence used."""
    reports = reports or []
    measured = _measured(model, reports)
    if measured:
        score = 0.7 * float(measured.get("judgement_accuracy") or 0) + 0.3 * float(measured.get("valid_plans") or 0)
        source = f"measured: foreman eval judgement {measured.get('judgement_accuracy')} / valid {measured.get('valid_plans')}"
    else:
        models = (evidence or {}).get("models") or {}
        indices = [entry.get("benchmarks", {}).get("intelligence_index") for entry in models.values() if isinstance(entry, dict)]
        indices = [value for value in indices if isinstance(value, (int, float))]
        mine = ((models.get(model) or {}).get("benchmarks") or {}).get("intelligence_index")
        tier = _tier_of(model, provider)
        size = _SIZE.search(model)
        if isinstance(mine, (int, float)) and indices:
            score, source = float(mine) / max(indices), f"benchmark: intelligence_index {mine} (best on record {max(indices)})"
        elif tier:
            score, source = TIER_SCORE.get(tier, 0.6), f"tier: {tier} in its provider's lineup"
        elif size:
            billions = float(size.group(1))
            score = 0.3 if billions < 20 else 0.5 if billions < 60 else 0.65
            source = f"size hint: {billions:g}B open-weight model"
        else:
            score, source = 0.5, "no evidence yet: run `orchestrate foreman eval`"
    band = "strong" if score >= 0.75 else "medium" if score >= 0.45 else "weak"
    return {"model": model, "score": round(score, 3), "band": band, "source": source}


def playbooks(path: Path | None = None) -> dict[str, dict[str, Any]]:
    merged = {band: dict(value) for band, value in PLAYBOOKS.items()}
    path = path or (Path.home() / ".agent-os" / "foreman-playbooks.json")
    try:
        override = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        override = {}
    for band, value in (override or {}).items():
        if band in merged and isinstance(value, dict):
            merged[band].update(value)
    return merged


def strategy_for(model: str, **kwargs: Any) -> dict[str, Any]:
    rated = strength(model, **kwargs)
    book = playbooks()[rated["band"]]
    return {**rated, "summary": book["summary"], "prioritize": book["prioritize"], "planner_addendum": book["planner_addendum"],
            "guard": bool(book["guard"]), "consult": bool(book["consult"])}


def strategy_table(registry=None, evidence: dict[str, Any] | None = None, reports: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Every registered model: planner strength, band and what to prioritize when it is the foreman."""
    if registry is None:
        from .router import ProviderRegistry

        registry = ProviderRegistry()
    if evidence is None:
        from . import model_value

        evidence = model_value.load_evidence()
    reports = _eval_reports(None) if reports is None else reports
    rows = []
    for provider in registry.providers:
        for tier, model in (provider.get("models") or {}).items():
            strategy = strategy_for(model, provider=provider, evidence=evidence, reports=reports)
            rows.append({"provider": provider["id"], "tier": tier, **{key: strategy[key] for key in ("model", "score", "band", "source", "summary", "prioritize")}})
    rows.sort(key=lambda row: -row["score"])
    return rows


def recommend(host: dict[str, Any], foreman_kind: str | None, foreman_model: str | None, registry=None) -> str | None:
    """One line: is the operator's own model a better foreman than the current one?"""
    active = host.get("active")
    info = (host.get("hosts") or {}).get(active or "")
    if not info:
        return None
    if registry is None:
        from .router import ProviderRegistry

        registry = ProviderRegistry()
    provider = registry.get(info["provider_hint"])
    mine = strength(info["model"], provider=provider, reports=_eval_reports(None))
    label = {"claude": "Claude", "chatgpt": "ChatGPT"}.get(active, active)
    if foreman_kind == active:
        return f"You are using {info['model']} ({mine['band']} planner) and it is the foreman: its planning is the best use of those tokens."
    if mine["band"] == "strong":
        return (f"You are using {info['model']} in {label}: a strong planner. Making {label} the foreman spends it on planning "
                f"(its best value per token) and sends the implementation to cheaper tiers.")
    return f"You are using {info['model']} in {label} ({mine['band']} planner): keep a stronger foreman for planning."


# ---------------------------------------------------------------------------
# 3. Deterministic plan guard (weak planners)
# ---------------------------------------------------------------------------


MAX_MERGED = 4


def _mergeable_class(task: dict[str, Any]) -> bool:
    """Only cheap tasks are folded together. A reasoning/frontier task is the
    plan's "decide once, let fast tasks implement" step: merging it with its
    implementation would move the cheap work onto the expensive model
    (measured: deepseek-v4-flash concurrency plan collapsed below its useful
    size and into one reasoning task)."""
    return task.get("capability_class") in (None, "fast", "balanced")


def _acyclic(tasks: list[dict[str, Any]]) -> bool:
    graph = {str(task.get("id")): [str(dep) for dep in task.get("depends_on") or []] for task in tasks if isinstance(task, dict)}
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return False
        if state.get(node) == 2 or node not in graph:
            return True
        state[node] = 1
        ok = all(visit(dep) for dep in graph[node])
        state[node] = 2
        return ok

    return all(visit(node) for node in graph)


def _fold(tasks: list[dict[str, Any]], chunk: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """``tasks`` with ``chunk`` folded into its first member; dependents rewired."""
    ids = [str(task.get("id")) for task in chunk]
    head = dict(chunk[0])
    classes = [task.get("capability_class") for task in chunk if task.get("capability_class") in CAPABILITY_CLASSES]
    efforts = [task.get("effort") for task in chunk if task.get("effort") in ("low", "medium", "high")]
    head["goal"] = " Then: ".join(str(task.get("goal") or "") for task in chunk)
    if classes:
        head["capability_class"] = max(classes, key=rank)
    if efforts:
        head["effort"] = max(efforts, key=("low", "medium", "high").index)
    validators = list(dict.fromkeys(item for task in chunk for item in (task.get("validators") or []) if isinstance(item, str)))
    if validators:
        head["validators"] = validators
    head["depends_on"] = list(dict.fromkeys(str(dep) for task in chunk for dep in (task.get("depends_on") or []) if str(dep) not in ids))
    head["scope"] = list(dict.fromkeys(str(path) for task in chunk for path in (task.get("scope") or [])))
    head.pop("ladder", None)
    folded = set(ids[1:])
    out = []
    for task in tasks:
        if not isinstance(task, dict):
            out.append(task)
            continue
        if str(task.get("id")) in folded:
            continue
        if str(task.get("id")) == ids[0]:
            task = head
        deps = [ids[0] if str(dep) in folded else str(dep) for dep in (task.get("depends_on") or [])]
        out.append({**task, "depends_on": [dep for dep in dict.fromkeys(deps) if dep != str(task.get("id"))]})
    return out


def merge_same_scope(structured: dict[str, Any] | None) -> tuple[dict[str, Any] | None, list[str]]:
    """Fold tasks that edit exactly the same files into one task.

    Same-scope tasks can never run in parallel (the engine serializes
    overlapping scopes), so splitting them only multiplies the per-task agent
    overhead (~15k input tokens per coding-CLI call). Measured: Opus and GPT
    foremen both split "tests for one function" into 4 tasks on one file.
    The merged task keeps the strongest class/effort, every validator and
    every outside dependency; dependents are rewired to it. A merge that would
    create a dependency cycle (A on X -> B on Y -> C on X) is skipped."""
    tasks = (structured or {}).get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 2:
        return structured, []
    groups: dict[tuple[str, ...], list[str]] = {}
    for task in tasks:
        if (isinstance(task, dict) and task.get("scope") and _mergeable_class(task)
                and task.get("role", "implementer") in ("implementer", "test_author")):
            groups.setdefault(tuple(sorted(map(str, task["scope"]))), []).append(str(task.get("id")))
    notes: list[str] = []
    current = list(tasks)
    for scope, member_ids in groups.items():
        for begin in range(0, len(member_ids), MAX_MERGED):
            chunk_ids = member_ids[begin:begin + MAX_MERGED]
            chunk = [task for task in current if isinstance(task, dict) and str(task.get("id")) in chunk_ids]
            if len(chunk) < 2:
                continue
            candidate = _fold(current, chunk)
            if not _acyclic(candidate):
                notes.append(f"merge skipped: folding {', '.join(chunk_ids)} would create a dependency cycle")
                continue
            current = candidate
            notes.append(f"merge: {', '.join(chunk_ids)} edit only {', '.join(scope)} -> one task {chunk_ids[0]}")
    if not any(note.startswith("merge:") for note in notes):
        return structured, notes
    return {**(structured or {}), "tasks": current}, notes


_TEST_PATH = re.compile(r"(^|/)(tests?/|test_[^/]*$|[^/]*_test\.[a-z]+$)")


def normalize_roles(structured: dict[str, Any] | None) -> tuple[dict[str, Any] | None, list[str]]:
    """Map roles the planner invented ("investigator", "designer") to the two
    the engine accepts, instead of rejecting the whole plan. Measured: a 14B
    foreman lost 2 of 7 plans to invented roles."""
    tasks = (structured or {}).get("tasks")
    if not isinstance(tasks, list):
        return structured, []
    notes, out = [], []
    for task in tasks:
        if isinstance(task, dict) and task.get("role") not in (None, "implementer", "test_author"):
            scope = [str(path) for path in task.get("scope") or []]
            role = "test_author" if scope and all(_TEST_PATH.search(path) for path in scope) else "implementer"
            notes.append(f"role: {task.get('id')} {task.get('role')!r} -> {role}")
            task = {**task, "role": role}
        out.append(task)
    return ({**(structured or {}), "tasks": out}, notes) if notes else (structured, [])


def merge_overlapping(structured: dict[str, Any] | None, max_files: int = 6) -> tuple[dict[str, Any] | None, list[str]]:
    """Fold tasks whose file scopes overlap (the engine serializes them anyway,
    so splitting them buys no parallelism and pays the per-agent overhead each
    time). Groups are connected components of the overlap graph, in plan
    order, capped at MAX_MERGED tasks and ``max_files`` files; cycle-safe."""
    from .model import scopes_overlap

    tasks = (structured or {}).get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 2:
        return structured, []
    eligible = [task for task in tasks if isinstance(task, dict) and task.get("scope") and _mergeable_class(task)
                and task.get("role", "implementer") in ("implementer", "test_author")]
    parent = {id(task): id(task) for task in eligible}

    def find(key: int) -> int:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    for index, first in enumerate(eligible):
        for second in eligible[index + 1:]:
            if scopes_overlap([str(path) for path in first["scope"]], [str(path) for path in second["scope"]]):
                parent[find(id(second))] = find(id(first))
    components: dict[int, list[dict[str, Any]]] = {}
    for task in eligible:
        components.setdefault(find(id(task)), []).append(task)
    notes: list[str] = []
    current = list(tasks)
    for members in components.values():
        chunk: list[dict[str, Any]] = []
        files: set[str] = set()
        groups = []
        for task in members:
            scope = {str(path) for path in task["scope"]}
            if chunk and (len(chunk) >= MAX_MERGED or len(files | scope) > max_files):
                groups.append(chunk)
                chunk, files = [], set()
            chunk.append(task)
            files |= scope
        groups.append(chunk)
        for group in groups:
            ids = [str(task.get("id")) for task in group]
            live = [task for task in current if isinstance(task, dict) and str(task.get("id")) in ids]
            if len(live) < 2:
                continue
            candidate = _fold(current, live)
            if not _acyclic(candidate):
                notes.append(f"merge skipped: folding {', '.join(ids)} would create a dependency cycle")
                continue
            current = candidate
            notes.append(f"merge: {', '.join(ids)} edit overlapping files -> one task {ids[0]}")
    if not any(note.startswith("merge:") for note in notes):
        return structured, notes
    return {**(structured or {}), "tasks": current}, notes


def apply(goal: str, structured: dict[str, Any] | None, strategy: dict[str, Any] | None) -> tuple[dict[str, Any] | None, list[str]]:
    """Every session-foreman plan gets role normalization and the same-scope
    merge; weak planners also get the class guard."""
    structured, notes = normalize_roles(structured)
    # Overlapping (not only identical) scopes: the engine serializes them anyway.
    # Re-scored on every live answer: never lower accuracy, fewer agent launches
    # for all four foremen on the held-out split (e.g. qwen3-235b 33% -> 50%).
    structured, merged = merge_overlapping(structured)
    notes += merged
    if (strategy or {}).get("guard"):
        structured, more = guard(goal, structured)
        notes += more
    return structured, notes


def guard(goal: str, structured: dict[str, Any] | None) -> tuple[dict[str, Any] | None, list[str]]:
    """Correct the capability classes of a plan without a model call.

    * Under-provisioning: the goal is design/concurrency/security work and no
      task is ``reasoning`` or stronger -> the first task whose own text is
      risky (else the first task) becomes ``reasoning``/``high``.
    * Over-provisioning: a ``balanced``+ task whose text is trivial (typo, docs,
      rename) and not risky -> ``fast``/``low``.
    """
    tasks = (structured or {}).get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return structured, []
    notes: list[str] = []
    tasks = [dict(task) if isinstance(task, dict) else task for task in tasks]
    for task in tasks:
        if not isinstance(task, dict):
            continue
        text = f"{task.get('goal', '')} {' '.join(map(str, task.get('scope') or []))}"
        cls = task.get("capability_class")
        if cls in CAPABILITY_CLASSES and cls != "deterministic" and rank(cls) >= rank("balanced") and TRIVIAL.search(text) and not RISKY.search(text):
            task.update(capability_class="fast", effort="low")
            notes.append(f"guard: {task.get('id')} {cls} -> fast (mechanical task)")
    classes = [task.get("capability_class") for task in tasks if isinstance(task, dict)]
    strong_enough = any(cls in CAPABILITY_CLASSES and cls != "deterministic" and rank(cls) >= rank("reasoning") for cls in classes)
    if RISKY.search(goal or "") and not strong_enough:
        target = next((task for task in tasks if isinstance(task, dict) and RISKY.search(f"{task.get('goal', '')}")), None)
        target = target or next((task for task in tasks if isinstance(task, dict)), None)
        if target is not None:
            notes.append(f"guard: {target.get('id')} {target.get('capability_class')} -> reasoning (the goal needs a design decision)")
            target.update(capability_class="reasoning", effort="high")
    return {**(structured or {}), "tasks": tasks}, notes
