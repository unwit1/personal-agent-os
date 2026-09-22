"""Continue Roadmap: find the next unfinished roadmap stage and work on it.

Everything before the first model call is deterministic and local:

1. read the repository (path, branch, uncommitted changes);
2. scan the roadmap markdown into stages with a status each;
3. look for unfinished work: orchestrated runs that never finished, and
   unmerged branches named after a roadmap stage (another agent's work);
4. load the latest handoff;
5. choose the stage and build a bounded goal that quotes only that stage's
   section of the roadmap, so the planner does not need to go and read it;
6. start (or resume) an orchestrated run.

Unfinished orchestrated work is resumed rather than re-planned, and a stage
with someone else's unmerged branch is skipped: both are duplicate-work
guards. A *campaign* (Auto Continue Until Done) repeats this after each run
completes and lands, until the roadmap has no eligible stage, a run needs the
user, or a guard trips.

Stage status comes from the roadmap's own ``Status:`` lines, so the
classification is only as good as the roadmap text. The chosen stage and the
line that decided it are shown to the user before any model runs.
"""

from __future__ import annotations

import json
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..storage import load_json, write_json
from ..timestamps import utc_now_iso as now
from .usage import ESTIMATE_METHOD, estimate_tokens


STATUSES = ("complete", "partial", "in_progress", "not_started", "deferred")
ELIGIBLE = ("partial", "in_progress", "not_started")
PLAIN_STATUS = {
    "complete": "done",
    "partial": "partly done",
    "in_progress": "in progress",
    "not_started": "not started",
    "deferred": "on hold",
}
_STAGE_ID = re.compile(r"^(P\d+(?:\.\d+)?[A-Z]?|EXEC-\d+(?:\.\d+)?)\b")
_HEADING = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
_DASHES = re.compile(r"\s+[—–-]+\s+")
MAX_EXCERPT_CHARS = 2600
MAX_RUNS_PER_STAGE = 2

STEPS = (
    ("read_repo", "Reading repository"),
    ("roadmap", "Checking roadmap"),
    ("unfinished", "Checking unfinished work"),
    ("handoff", "Loading previous handoff"),
    ("choose", "Choosing the next task and agent"),
    ("start", "Starting work"),
)


class RoadmapError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def classify(section: str) -> tuple[str, str | None]:
    """Status of one roadmap section and the line that decided it."""
    status_line = None
    for line in section.splitlines():
        if line.strip().casefold().startswith("status:"):
            status_line = line.strip()
            break
    if status_line:
        text = status_line.casefold()
        if "deferred" in text or "on hold" in text:
            return "deferred", status_line
        if "foundation" in text or "partial" in text or "steps " in text:
            return "partial", status_line
        if "complete" in text or "implemented" in text or "done" in text:
            return "complete", status_line
        return "in_progress", status_line
    for line in section.splitlines():
        if re.match(r"^Current (bounded|deterministic)", line.strip()):
            return "in_progress", line.strip()[:200]
    return "not_started", None


def parse(text: str) -> list[dict[str, Any]]:
    """Stages from roadmap markdown, in document (priority) order.

    A stage is a ``###`` heading inside a ``## P<n>`` section, or a ``## P<n>``
    section that has no ``###`` stages of its own.
    """
    lines = text.splitlines()
    headings = []
    for index, line in enumerate(lines):
        match = _HEADING.match(line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))
    stages: list[dict[str, Any]] = []
    for position, (index, level, title) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        stage_id_match = _STAGE_ID.match(title)
        if level == 2:
            if not stage_id_match:
                continue
            has_children = position + 1 < len(headings) and headings[position + 1][1] == 3
            if has_children:
                continue
        else:
            parent = next((h for h in reversed(headings[:position]) if h[1] == 2), None)
            if not stage_id_match and not (parent and _STAGE_ID.match(parent[2])):
                continue
        body = "\n".join(lines[index:end]).strip()
        body = re.sub(r"\n-{3,}\s*$", "", body).strip()
        if stage_id_match:
            stage_id = stage_id_match.group(1)
            name = _DASHES.split(title, maxsplit=1)[-1] if _DASHES.search(title) else title[len(stage_id):].strip(" —–-")
        else:
            parent_id = _STAGE_ID.match(parent[2]).group(1)  # type: ignore[index]
            stage_id = f"{parent_id}:{re.sub(r'[^a-z0-9]+', '-', title.casefold()).strip('-')[:24]}"
            name = title
        status, evidence = classify(body)
        stages.append(
            {
                "id": stage_id,
                "title": name.strip(),
                "status": status,
                "plain_status": PLAIN_STATUS[status],
                "evidence": evidence,
                "line": index + 1,
                "chars": len(body),
                "excerpt": body,
            }
        )
    return stages


def roadmap_path(project_id: str | None, repository: Path) -> Path | None:
    """The project's master roadmap, from its state file's important paths."""
    candidates: list[str] = []
    if project_id:
        try:
            from ..registry import get_project, load_state

            state = load_state(get_project(project_id))
            paths = [str(item) for item in state.get("important_paths") or []]
            candidates += [item for item in paths if "roadmap" in item.casefold() and "master" in item.casefold() and item.endswith(".md")]
            candidates += [item for item in paths if "roadmap" in item.casefold() and item.endswith(".md")]
        except Exception:
            pass
    candidates += ["ROADMAP.md", "docs/ROADMAP.md", "docs/roadmap.md", "roadmap.md"]
    for item in candidates:
        path = repository / item
        if path.is_file():
            return path
    return None


def scan(project_id: str | None, repository: Path | str) -> dict[str, Any]:
    repository = Path(repository)
    path = roadmap_path(project_id, repository)
    if path is None:
        return {"found": False, "path": None, "stages": [], "total": 0, "complete": 0, "counts": {}, "candidate_chars": 0}
    text = path.read_text(encoding="utf-8", errors="replace")
    stages = parse(text)
    counts = {status: sum(1 for stage in stages if stage["status"] == status) for status in STATUSES}
    related = [item for item in path.parent.glob("*.md") if item != path]
    related_chars = sum(item.stat().st_size for item in related)
    return {
        "found": True,
        "path": str(path),
        "relative_path": path.relative_to(repository).as_posix() if path.is_relative_to(repository) else str(path),
        "stages": stages,
        "total": len(stages),
        "complete": counts["complete"],
        "counts": counts,
        # Candidate context: the master roadmap plus the detailed roadmaps next
        # to it -- what "go read the roadmap" hands a model.
        "candidate_items": 1 + len(related),
        "candidate_chars": len(text) + related_chars,
    }


# ---------------------------------------------------------------------------
# Unfinished work
# ---------------------------------------------------------------------------

UNFINISHED_STATES = frozenset({"CREATED", "PLANNING", "READY", "RUNNING", "VALIDATING", "REVIEWING", "INTEGRATING", "APPROVAL_REQUIRED", "PAUSED", "BLOCKED"})


def unfinished_runs(engine: Any, project_id: str | None, repository: Path | None = None) -> list[dict[str, Any]]:
    """Orchestrated runs for this project that never reached COMPLETE and were
    not abandoned, newest first."""
    runs = []
    for item in engine.list_runs():
        if item.get("state") not in UNFINISHED_STATES:
            continue
        try:
            record = engine.load(item["run_id"])
        except Exception:
            continue
        if (record.get("origin") or {}).get("abandoned"):
            continue
        same_project = project_id and record.get("project") == project_id
        same_repo = repository is not None and Path(record.get("repository") or "") == Path(repository)
        if same_project or same_repo:
            runs.append({**item, "origin": record.get("origin") or {}, "driver": engine.store.driver(item["run_id"])})
    return runs


def stage_branches(repository: Path, stages: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Unmerged local branches whose name mentions a stage id, e.g.
    ``p0.4-recovery`` for P0.4. Orchestrator branches are excluded."""
    from .worktrees import git

    try:
        base = git(["rev-parse", "--abbrev-ref", "HEAD"], repository, check=False).stdout.strip() or "HEAD"
        output = git(["branch", "--no-merged", base, "--format=%(refname:short)"], repository, check=False).stdout
    except Exception:
        return {}
    branches = [line.strip() for line in output.splitlines() if line.strip() and not line.strip().startswith("agent-os/")]
    found: dict[str, list[str]] = {}
    for stage in stages:
        if ":" in stage["id"]:
            continue
        token = stage["id"].casefold()
        variants = {token, token.replace(".", "-"), token.replace(".", "_")}
        for branch in branches:
            name = branch.casefold()
            if any(re.search(rf"(^|[/_-]){re.escape(variant)}([._/-]|$)", name) for variant in variants):
                found.setdefault(stage["id"], []).append(branch)
    return found


def choose_stage(stages: list[dict[str, Any]], branches: dict[str, list[str]], skip: set[str] | None = None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Earliest eligible stage; stages with someone else's unmerged branch are
    skipped (and reported)."""
    skipped = []
    for stage in stages:
        if stage["status"] not in ELIGIBLE or stage["id"] in (skip or set()):
            continue
        if branches.get(stage["id"]):
            skipped.append({"stage": stage["id"], "reason": f"unfinished work already exists on branch {', '.join(branches[stage['id']])}"})
            continue
        return stage, skipped
    return None, skipped


# ---------------------------------------------------------------------------
# Goal
# ---------------------------------------------------------------------------


def build_goal(project: str | None, stage: dict[str, Any], roadmap_rel: str, handoff: dict[str, Any] | None) -> str:
    excerpt = stage["excerpt"]
    if len(excerpt) > MAX_EXCERPT_CHARS:
        excerpt = excerpt[:MAX_EXCERPT_CHARS].rsplit("\n", 1)[0] + "\n[... section continues in the roadmap file ...]"
    remaining = [str(item)[:200] for item in (handoff or {}).get("remaining") or []][:4]
    lines = [
        f"Continue the {project or 'project'} roadmap: stage {stage['id']} — {stage['title']}.",
        f"Roadmap status: {stage['evidence'] or 'no status line (not started)'}",
        "",
        "Do the next bounded slice of this stage that can be finished and validated now; skip anything the status says is done.",
        f"The roadmap section is quoted below and is authoritative: do not re-read {roadmap_rel} to find it.",
        "If the remaining work needs a human design decision, report status needs_decision with the question instead of guessing.",
        f"The last task must update this stage's Status/Current text in {roadmap_rel} to say what is now complete.",
    ]
    if remaining:
        lines += ["", "Open items from the latest handoff:", *[f"- {item}" for item in remaining]]
    lines += ["", "Roadmap section:", excerpt]
    return "\n".join(lines)[:3900]


# ---------------------------------------------------------------------------
# Preparation (Continue Roadmap)
# ---------------------------------------------------------------------------


class Preparation:
    """Visible, step-by-step progress for one Continue Roadmap press."""

    def __init__(self, prep_id: str | None = None, on_change: Callable[["Preparation"], None] | None = None) -> None:
        self.id = prep_id or f"prep-{uuid.uuid4().hex[:8]}"
        self.steps = [{"id": key, "label": label, "status": "pending", "detail": None, "at": None} for key, label in STEPS]
        self.state = "running"
        self.message = "Starting roadmap run..."
        self.result: dict[str, Any] | None = None
        self.started_at = now()
        self._on_change = on_change

    def step(self, key: str, status: str, detail: str | None = None) -> None:
        for item in self.steps:
            if item["id"] == key:
                item.update(status=status, detail=detail, at=now())
                if status == "active":
                    self.message = f"{item['label']}..."
        self._changed()

    def finish(self, state: str, message: str, result: dict[str, Any] | None = None) -> None:
        self.state = state
        self.message = message
        self.result = result
        for item in self.steps:
            if item["status"] == "active":
                item["status"] = "done" if state == "done" else "failed"
        self._changed()

    def view(self) -> dict[str, Any]:
        return {"id": self.id, "state": self.state, "message": self.message, "steps": self.steps, "result": self.result, "started_at": self.started_at}

    def _changed(self) -> None:
        if self._on_change:
            try:
                self._on_change(self)
            except Exception:
                pass


def continue_roadmap(
    engine: Any,
    project: str | None = None,
    repository: str | Path | None = None,
    *,
    auto_until_done: bool = False,
    preference: str | None = None,
    fresh: bool = False,
    skip: set[str] | None = None,
    prep: Preparation | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One press of Continue Roadmap. Never raises for expected outcomes; the
    result's ``action`` says what happened:

    ``started`` (new run), ``resumed`` (unfinished run continued),
    ``needs_attention`` (an unfinished run is waiting for the user),
    ``nothing_to_do`` (no eligible stage), ``error``.
    """
    prep = prep or Preparation()
    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
    ledger = engine.ledger
    try:
        # 1. repository
        prep.step("read_repo", "active")
        project_id, repo = engine._resolve_target(repository, project)
        from .worktrees import current_branch, is_dirty

        dirty = is_dirty(repo)
        prep.step("read_repo", "done", f"{project_id or repo.name} on {current_branch(repo) or 'detached HEAD'}" + (" (has uncommitted changes)" if dirty else ""))

        # 2. roadmap
        prep.step("roadmap", "active")
        scanned = scan(project_id, repo)
        if not scanned["found"]:
            prep.step("roadmap", "failed", "no roadmap file found")
            result = {"action": "error", "message": "I could not find a roadmap for this project. Add ROADMAP.md or list it in the project's important paths."}
            prep.finish("failed", result["message"], result)
            return result
        prep.step("roadmap", "done", f"{scanned['complete']} of {scanned['total']} stages complete")

        # 3. unfinished work
        prep.step("unfinished", "active")
        pending = unfinished_runs(engine, project_id, repo)
        if pending and fresh:
            for item in pending:
                _abandon(engine, item["run_id"], "replaced by a fresh Continue Roadmap run")
            pending = []
        if pending:
            current = pending[0]
            prep.step("unfinished", "done", f"found unfinished run {current['run_id']} ({current['state']})")
            return _resume(engine, current, prep, auto_until_done, project_id, scanned)
        branches = stage_branches(repo, scanned["stages"])
        stage, skipped = choose_stage(scanned["stages"], branches, skip)
        detail = "none found" if not skipped else "; ".join(f"skipped {item['stage']}: {item['reason']}" for item in skipped)
        prep.step("unfinished", "done", detail)

        # From here on the run id is known: record the deterministic work.
        ledger.emit(run_id, "run_started", mode="Continue Roadmap", project=project_id, auto_until_done=auto_until_done)
        ledger.emit(run_id, "local_execution", what="scanned the roadmap and repository without a model", roadmap=scanned["relative_path"], stages=scanned["total"])
        ledger.emit(run_id, "roadmap_scanned", total=scanned["total"], complete=scanned["complete"], counts=scanned["counts"], path=scanned["relative_path"])
        for item in skipped:
            ledger.emit(run_id, "loop_guard", guard="duplicate_roadmap_work", reason=f"{item['stage']}: {item['reason']}")

        if stage is None:
            result = {"action": "nothing_to_do", "message": "Every eligible roadmap stage is complete. Nothing to do.", "roadmap": _roadmap_view(scanned)}
            ledger.emit(run_id, "work_avoided", category="nothing_to_do", model_calls_avoided=1, reason="the roadmap has no eligible stage, so no planner was started", tokens_avoided_estimate=None)
            prep.step("handoff", "skipped")
            prep.step("choose", "done", "no eligible stage")
            prep.step("start", "skipped")
            prep.finish("done", result["message"], result)
            return result

        # 4. handoff
        prep.step("handoff", "active")
        handoff = _latest_handoff(project_id)
        ledger.emit(run_id, "handoff_loaded", found=bool(handoff), created_at=(handoff or {}).get("created_at"), remaining=len((handoff or {}).get("remaining") or []))
        prep.step("handoff", "done", f"from {handoff.get('created_at', '')[:10]}" if handoff else "none")

        # 5. choose
        prep.step("choose", "active")
        goal = build_goal(project_id, stage, scanned["relative_path"], handoff)
        # Roadmap content actually quoted in the goal (the rest is instructions).
        excerpt_chars = min(len(stage["excerpt"]), MAX_EXCERPT_CHARS, len(goal))
        ledger.emit(run_id, "task_selected", stage_id=stage["id"], title=stage["title"], status=stage["status"], evidence=stage["evidence"])
        ledger.emit(
            run_id, "context_selected", "roadmap",
            method=f"candidate = master roadmap + detailed roadmaps in the same folder; selected = this stage's section in the goal; tokens by {ESTIMATE_METHOD}",
            candidate_items=scanned["candidate_items"], selected_items=1,
            candidate_tokens_estimate=estimate_tokens(scanned["candidate_chars"]),
            selected_tokens_estimate=estimate_tokens(excerpt_chars),
            reduction_pct=round(100.0 * (1 - excerpt_chars / scanned["candidate_chars"]), 1) if scanned["candidate_chars"] else None,
            instruction_chars=len(goal) - excerpt_chars,
        )
        run_policy = {"planning": "auto", "auto_continue": True, "final_integration": "merge_to_base", **(policy or {})}
        if preference:
            run_policy["preference"] = preference
        if not run_policy.get("default_validators") and not _has_project_validators(project_id):
            detected = detect_validators(repo)
            if detected:
                run_policy["default_validators"] = detected
                ledger.emit(run_id, "local_execution", what="found the project's tests: " + detected[0]["name"])
        prep.step("choose", "done", f"{stage['id']} — {stage['title']}")

        # 6. start
        prep.step("start", "active")
        summary = engine.create_run(
            goal, repository=str(repo), project=project_id, policy=run_policy, run_id=run_id,
            origin={"kind": "roadmap", "stage_id": stage["id"], "stage_title": stage["title"], "stage_status": stage["status"], "auto_until_done": auto_until_done, "prep": prep.id},
        )
        summary = engine.start(summary["run_id"], True)
        _campaign_update(engine, project_id or repo.name, auto_until_done=auto_until_done, current_run=run_id, stage_id=stage["id"])
        prep.step("start", "done", "planner starting")
        result = {"action": "started", "run_id": run_id, "stage": _stage_view(stage), "message": f"Started {stage['id']} — {stage['title']}", "roadmap": _roadmap_view(scanned)}
        prep.finish("done", result["message"], result)
        return result
    except Exception as exc:
        message = f"Continue Roadmap could not start: {type(exc).__name__}: {exc}"[:400]
        result = {"action": "error", "message": message}
        prep.finish("failed", message, result)
        return result


def _resume(engine: Any, current: dict[str, Any], prep: Preparation, auto_until_done: bool, project_id: str | None, scanned: dict[str, Any]) -> dict[str, Any]:
    run_id = current["run_id"]
    prep.step("handoff", "skipped", "continuing the unfinished run instead")
    ledger = engine.ledger
    record = engine.load(run_id)
    ledger.emit(run_id, "roadmap_scanned", total=scanned["total"], complete=scanned["complete"], counts=scanned["counts"], path=scanned.get("relative_path"))
    view = {"run_id": run_id, "goal": str(record.get("goal", ""))[:200], "state": record["state"], "roadmap": _roadmap_view(scanned)}
    if record["state"] in {"APPROVAL_REQUIRED", "BLOCKED"}:
        prep.step("choose", "done", "the unfinished run needs you first")
        prep.step("start", "skipped")
        result = {"action": "needs_attention", "message": "An earlier run is waiting for you. Nothing new was started.", **view}
        prep.finish("done", result["message"], result)
        return result
    planner = record["nodes"].get("plan")
    measured = ((planner or {}).get("result") or {}).get("usage") or {}
    reused_plan = bool(planner and planner["state"] == "PASSED")
    ledger.emit(
        run_id, "work_avoided", category="resume", model_calls_avoided=1 if reused_plan else 0,
        reason="continued the unfinished run and its saved progress instead of planning the work again",
        tokens_avoided_estimate=(int(measured.get("input_tokens") or 0) + int(measured.get("output_tokens") or 0)) if reused_plan and measured.get("accuracy") == "exact" and measured.get("source") != "synthetic" else None,
        estimate_basis="measured tokens of the original planner call" if reused_plan and measured.get("accuracy") == "exact" else None,
    )
    prep.step("choose", "done", "continuing where it stopped")
    prep.step("start", "active")
    engine.resume(run_id, True)
    _campaign_update(engine, project_id or "unregistered", auto_until_done=auto_until_done, current_run=run_id, stage_id=(record.get("origin") or {}).get("stage_id"))
    prep.step("start", "done", "resumed")
    result = {"action": "resumed", "message": "Resumed the unfinished run.", **view}
    prep.finish("done", result["message"], result)
    return result


def _abandon(engine: Any, run_id: str, reason: str) -> None:
    try:
        engine.stop(run_id)
    except Exception:
        pass
    with engine._lock:
        record = engine.load(run_id)
        origin = dict(record.get("origin") or {})
        origin.update(abandoned=True, abandoned_reason=reason, abandoned_at=now())
        record["origin"] = origin
        engine.store.save(record)
    engine.ledger.emit(run_id, "note", text=f"Set aside: {reason}")


def _has_project_validators(project_id: str | None) -> bool:
    if not project_id:
        return False
    try:
        from ..registry import get_project, load_state

        return bool(load_state(get_project(project_id)).get("validation_commands"))
    except Exception:
        return False


def detect_validators(repo: Path) -> list[dict[str, Any]]:
    """A test command for a project with none registered: Python unittest
    discovery when ``tests/test_*.py`` exists. Without one, integration asks
    the user (no evidence, no automatic merge)."""
    import sys

    if (repo / "tests").is_dir() and any((repo / "tests").glob("test_*.py")):
        return [{"kind": "command", "command": [sys.executable, "-m", "unittest", "discover", "-s", "tests"], "name": "unit tests (tests/ discovered)"}]
    return []


def _latest_handoff(project_id: str | None) -> dict[str, Any] | None:
    if not project_id:
        return None
    try:
        from ..compiler import latest_handoff

        handoff = latest_handoff(project_id)
    except Exception:
        return None
    if not handoff:
        return None
    return {"created_at": handoff.get("created_at"), "remaining": handoff.get("remaining") or []}


def _stage_view(stage: dict[str, Any]) -> dict[str, Any]:
    return {key: stage[key] for key in ("id", "title", "status", "plain_status", "evidence")}


def _roadmap_view(scanned: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": scanned.get("relative_path"),
        "total": scanned["total"],
        "complete": scanned["complete"],
        "counts": scanned["counts"],
        "stages": [_stage_view(stage) for stage in scanned["stages"]],
    }


def overview(engine: Any, project: str | None = None, repository: str | Path | None = None) -> dict[str, Any]:
    """Read-only home-screen data: roadmap progress, next stage, unfinished work."""
    project_id, repo = engine._resolve_target(repository, project)
    from .worktrees import current_branch, is_dirty

    scanned = scan(project_id, repo)
    branches = stage_branches(repo, scanned["stages"]) if scanned["found"] else {}
    stage, skipped = choose_stage(scanned["stages"], branches)
    return {
        "project": project_id,
        "repository": str(repo),
        "branch": current_branch(repo),
        "dirty": is_dirty(repo),
        "roadmap": _roadmap_view(scanned) if scanned["found"] else None,
        "next_stage": _stage_view(stage) if stage else None,
        "skipped": skipped,
        "stage_branches": branches,
        "unfinished_runs": unfinished_runs(engine, project_id, repo),
        "campaign": load_campaign(engine, project_id or repo.name),
    }


# ---------------------------------------------------------------------------
# Campaign: Auto Continue Until Done
# ---------------------------------------------------------------------------


def _campaign_path(engine: Any, key: str) -> Path:
    return engine.store.home / "campaigns" / f"{re.sub(r'[^A-Za-z0-9_.-]+', '-', key)}.json"


def load_campaign(engine: Any, key: str) -> dict[str, Any] | None:
    try:
        return load_json(_campaign_path(engine, key))
    except (OSError, json.JSONDecodeError):
        return None


def _campaign_update(engine: Any, key: str, **fields: Any) -> dict[str, Any]:
    campaign = load_campaign(engine, key) or {"project": key, "runs": [], "created_at": now(), "status": "active"}
    run_id = fields.get("current_run")
    if run_id and run_id not in [item["run_id"] for item in campaign["runs"]]:
        campaign["runs"].append({"run_id": run_id, "stage_id": fields.get("stage_id"), "started_at": now(), "outcome": None})
    campaign.update({key_: value for key_, value in fields.items() if key_ != "stage_id"})
    campaign["status"] = fields.get("status", "active")
    campaign["updated_at"] = now()
    write_json(_campaign_path(engine, key), campaign)
    return campaign


def drive_campaign(
    engine: Any,
    project: str | None = None,
    repository: str | Path | None = None,
    *,
    max_runs: int = 10,
    should_stop: Callable[[], bool] | None = None,
    run_driver: Callable[[str], dict[str, Any]] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Drive the project's current run; when it completes (and landed), start
    the next roadmap stage, until something needs the user."""
    project_id, repo = engine._resolve_target(repository, project)
    key = project_id or repo.name
    drive = run_driver or (lambda run_id: engine.run_loop(run_id, owner="campaign"))
    started_runs = 0
    while True:
        campaign = load_campaign(engine, key) or {}
        run_id = campaign.get("current_run")
        if not run_id:
            return _campaign_stop(engine, key, "idle", "no current run")
        summary = drive(run_id)
        state = summary["state"]
        _record_outcome(engine, key, run_id, state)
        if state != "COMPLETE":
            return _campaign_stop(engine, key, "waiting", f"run {run_id} is {state}")
        landed = (summary.get("final") or {}).get("landed") or {}
        if (summary.get("final") or {}).get("summary") and landed and not landed.get("ok"):
            return _campaign_stop(engine, key, "waiting", f"the finished work was not added to the main branch: {landed.get('reason')}")
        if not campaign.get("auto_until_done"):
            return _campaign_stop(engine, key, "done", "run complete; Auto Continue Until Done is off")
        if should_stop and should_stop():
            return _campaign_stop(engine, key, "paused", "stopped by user")
        if started_runs >= max_runs:
            engine.ledger.emit(run_id, "loop_guard", guard="campaign_run_limit", reason=f"campaign started {max_runs} runs; stopping for review")
            return _campaign_stop(engine, key, "waiting", f"reached the limit of {max_runs} runs in one go")
        # A stage that has finished MAX_RUNS_PER_STAGE runs in this campaign and
        # is still not marked complete in the roadmap is not picked again.
        finished: dict[str, int] = {}
        for item in (load_campaign(engine, key) or {}).get("runs", []):
            if item.get("stage_id") and item.get("outcome") == "COMPLETE":
                finished[item["stage_id"]] = finished.get(item["stage_id"], 0) + 1
        skip = {stage for stage, count in finished.items() if count >= MAX_RUNS_PER_STAGE}
        for stage in sorted(skip):
            engine.ledger.emit(run_id, "loop_guard", guard="stage_repeat", reason=f"{stage} finished {finished[stage]} runs without being marked complete; not picking it again")
        result = continue_roadmap(engine, project_id, repo, auto_until_done=True, skip=skip, policy=policy)
        started_runs += 1
        if result["action"] not in {"started", "resumed"}:
            return _campaign_stop(engine, key, "done" if result["action"] == "nothing_to_do" else "waiting", result["message"])


def _record_outcome(engine: Any, key: str, run_id: str, state: str) -> None:
    campaign = load_campaign(engine, key)
    if not campaign:
        return
    for item in campaign["runs"]:
        if item["run_id"] == run_id:
            item["outcome"] = state
    write_json(_campaign_path(engine, key), campaign)


def _campaign_stop(engine: Any, key: str, status: str, reason: str) -> dict[str, Any]:
    campaign = load_campaign(engine, key) or {"project": key, "runs": []}
    campaign.update(status=status, stop_reason=reason, updated_at=now())
    write_json(_campaign_path(engine, key), campaign)
    return campaign


class CampaignThreads:
    """Background campaign drivers owned by one process (the GUI server)."""

    def __init__(self) -> None:
        self._threads: dict[str, threading.Thread] = {}
        self._stop: dict[str, bool] = {}
        self.errors: dict[str, str] = {}
        self._lock = threading.Lock()

    def alive(self, key: str) -> bool:
        thread = self._threads.get(key)
        return bool(thread and thread.is_alive())

    def ensure(self, engine: Any, project: str | None, repository: str | None = None) -> bool:
        key = project or str(repository)
        with self._lock:
            if self.alive(key):
                return False
            self._stop[key] = False
            self.errors.pop(key, None)

            def run() -> None:
                try:
                    drive_campaign(engine, project, repository, should_stop=lambda: self._stop.get(key, False))
                except Exception as exc:
                    self.errors[key] = f"{type(exc).__name__}: {exc}"[:400]

            thread = threading.Thread(target=run, name=f"agent-os-campaign-{key}", daemon=True)
            self._threads[key] = thread
            thread.start()
            return True

    def request_stop(self, key: str) -> None:
        self._stop[key] = True


def wait_for(predicate: Callable[[], bool], timeout: float, interval: float = 0.05) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()
