"""The orchestration engine: scheduler, auto-continue controller, gates.

One ``step`` is one deterministic tick over persisted run state:

    reconcile -> honour stop/pause -> poll workers -> collect + validate
    -> review / repair routing -> integrate validated work -> dispatch
    runnable nodes -> completion check -> derive run state -> persist

``run_loop`` repeats ticks. With ``auto_continue`` it keeps going until the run
is COMPLETE, PAUSED, APPROVAL_REQUIRED, or BLOCKED; without it, it stops at the
next stage boundary (a node passing), like the staged workflow runner.

The engine never trusts an agent's self-report: validators decide whether work
passed, independent review decides whether it is acceptable, and integration
refuses anything that has not cleared both. A provider failure is a routing
event -- the unfinished node keeps its worktree and checkpoint and moves to an
allowed alternative -- not a reason to abandon the run.
"""

from __future__ import annotations

import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..capabilities import next_class
from ..telemetry import LocalTelemetryStore, TelemetryEvent, TelemetryPrivacyError
from ..timestamps import utc_now_iso as now
from . import planner, prompts
from .adapters import AgentLaunchRequest, AgentResult, RunningAgent, get_adapter
from .adapters.base import kill_tree
from .model import (
    ACTIVE_NODE_STATES,
    DISPATCHABLE_NODE_STATES,
    INTEGRATED_ROLES,
    PROVIDER_FAILURES,
    RUN_SCHEMA,
    STOP_STATES,
    PlanError,
    check_identifier,
    merge_policy,
    new_node,
    scopes_overlap,
)
from .review import MalformedReview, apply_dispositions, material, parse_review
from .router import ProviderRegistry, load_key, select
from .store import RunStore, pid_alive, redact
from .validators import run_all
from .worktrees import GitError, WorktreeManager, current_branch, head_commit, is_dirty, repository_root


MAX_FAILURES_KEPT = 10
MAX_EVENTS_IN_SUMMARY = 30
_LABEL_CLEAN = re.compile(r"[^a-z0-9_.-]+")


class OrchestratorError(ValueError):
    pass


def _label(value: Any) -> str | None:
    text = _LABEL_CLEAN.sub("-", str(value or "").casefold()).strip("-._")[:64]
    return text or None


class Orchestrator:
    def __init__(
        self,
        store: RunStore | None = None,
        *,
        registry: ProviderRegistry | None = None,
        registry_path: Path | None = None,
        telemetry_store: LocalTelemetryStore | None = None,
        claims_path: Path | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.store = store or RunStore()
        self._registry = registry
        self._registry_path = registry_path
        self._telemetry = telemetry_store
        self._claims_path = claims_path
        self._sleep = sleep
        self._handles: dict[tuple[str, str], RunningAgent] = {}
        self._adapters: dict[str, Any] = {}
        self._availability: dict[str, bool] | None = None
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------

    def registry(self) -> ProviderRegistry:
        if self._registry is None:
            self._registry = ProviderRegistry(self._registry_path)
        return self._registry

    def reload_providers(self) -> dict[str, Any]:
        with self._lock:
            if self._registry_path is not None or self._registry is None or self._registry.path != "<inline>":
                self._registry = None
            self._adapters.clear()
            self._availability = None
            return self.providers()

    def _adapter(self, provider_id: str) -> Any:
        if provider_id not in self._adapters:
            provider = self.registry().get(provider_id)
            if provider is None:
                raise OrchestratorError(f"provider {provider_id} is not configured")
            self._adapters[provider_id] = get_adapter(provider)
        return self._adapters[provider_id]

    def availability(self) -> dict[str, bool]:
        if self._availability is None:
            result: dict[str, bool] = {}
            for provider in self.registry().providers:
                if not provider["enabled"]:
                    result[provider["id"]] = False
                    continue
                try:
                    result[provider["id"]] = bool(self._adapter(provider["id"]).probe().available)
                except Exception:
                    result[provider["id"]] = False
            self._availability = result
        return self._availability

    def providers(self) -> dict[str, Any]:
        registry = self.registry()
        described = registry.describe()
        for entry in described["providers"]:
            try:
                status = self._adapter(entry["id"]).probe()
                entry["probe"] = {"available": status.available, "version": status.version, "reason": status.reason}
            except Exception as exc:
                entry["probe"] = {"available": False, "version": None, "reason": redact(exc, 200)}
        described["recommendations"] = {}
        for role, capability, effort in (
            ("planner", "balanced", "medium"),
            ("implementer", "balanced", "medium"),
            ("reviewer", "balanced", "medium"),
            ("implementer", "reasoning", "high"),
        ):
            choice = select(registry, capability_class=capability, effort=effort, role=role, availability=self.availability())
            described["recommendations"][f"{role}:{capability}:{effort}"] = {
                key: choice.get(key) for key in ("resolved", "provider", "model", "provider_effort", "reason")
            }
        return described

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create_run(
        self,
        goal: str,
        *,
        repository: str | Path | None = None,
        project: str | None = None,
        tasks: list[dict[str, Any]] | None = None,
        policy: dict[str, Any] | None = None,
        overrides: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        goal = str(goal or "").strip()
        if not goal:
            raise OrchestratorError("a run needs a goal")
        project_id, repo = self._resolve_target(repository, project)
        identifier = check_identifier(run_id, "run id") if run_id else (
            f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
        )
        if self.store.exists(identifier):
            raise OrchestratorError(f"run already exists: {identifier}")
        run_policy = merge_policy(policy)
        if not run_policy["default_validators"] and project_id:
            run_policy["default_validators"] = _project_validators(project_id)
        if tasks:
            nodes = planner.explicit_plan(tasks, run_policy["max_planned_tasks"])
            planning = "explicit"
        elif run_policy["planning"] == "single":
            nodes = planner.single_plan(goal, run_policy["default_validators"])
            planning = "single"
        elif run_policy["planning"] == "explicit":
            raise OrchestratorError("planning=explicit needs tasks")
        else:
            nodes = planner.planner_plan(goal, run_policy["planner_capability_class"], run_policy["planner_effort"])
            planning = "auto"
        dirty = is_dirty(repo)
        record: dict[str, Any] = {
            "schema": RUN_SCHEMA,
            "run_id": identifier,
            "goal": goal[:4000],
            "project": project_id,
            "repository": str(repo),
            "base_ref": current_branch(repo),
            "base_commit": head_commit(repo),
            "preflight": {
                "dirty_worktree": dirty,
                "note": "uncommitted changes in the base checkout are not visible to workers" if dirty else None,
                "planning": planning,
            },
            "policy": run_policy,
            "state": "CREATED",
            "state_reason": None,
            "control": {"started": False, "paused": False, "stop_requested": False},
            "overrides": _clean_overrides(overrides),
            "nodes": nodes,
            "order": list(nodes),
            "gates": [],
            "worktree_layout": "short",
            "launches": 0,
            "launch_budget": run_policy["max_launches"],
            "integration": {"branch": None, "path": None, "head": None, "merged": []},
            "final": {"validation": None, "repairs": 0, "landed": None, "summary": None},
            "usage": {"input_tokens": 0, "cached_tokens": 0, "output_tokens": 0, "workers": 0},
            "created_at": now(),
            "updated_at": now(),
        }
        self.store.save(record)
        self.store.append_event(identifier, "run.created", detail=f"{planning} plan with {len(nodes)} node(s)")
        return self.summary(record)

    def _resolve_target(self, repository: str | Path | None, project: str | None) -> tuple[str | None, Path]:
        from ..machine import resolve_path
        from ..registry import get_project, identify_project

        project_id = None
        if project:
            record = get_project(project)
            project_id = record["id"]
            if repository is None:
                path, _ = resolve_path(record)
                repository = path
        if repository is None:
            raise OrchestratorError("a run needs a repository path or a registered project")
        try:
            repo = repository_root(Path(repository).expanduser())
        except GitError as exc:
            raise OrchestratorError(f"{repository} is not inside a Git repository") from exc
        if project_id is None:
            try:
                identified = identify_project(repo)
            except Exception:
                identified = None
            project_id = identified["id"] if identified else None
        return project_id, repo

    # ------------------------------------------------------------------
    # Public controls
    # ------------------------------------------------------------------

    def load(self, run_id: str) -> dict[str, Any]:
        return self.store.load(run_id)

    def start(self, run_id: str, auto_continue: bool | None = None) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            if auto_continue is not None:
                record["policy"]["auto_continue"] = bool(auto_continue)
            record["control"]["started"] = True
            record["control"]["paused"] = False
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "run.started", detail=f"auto_continue={record['policy']['auto_continue']}")
            return self.summary(record)

    def set_auto_continue(self, run_id: str, enabled: bool) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            record["policy"]["auto_continue"] = bool(enabled)
            self.store.save(record)
            self.store.append_event(run_id, "run.auto_continue", detail=str(bool(enabled)))
            return self.summary(record)

    def pause(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            record["control"]["paused"] = True
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "run.paused", detail="no new work will be dispatched")
            return self.summary(record)

    def resume(self, run_id: str, auto_continue: bool | None = None) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            record["control"]["paused"] = False
            record["control"]["stop_requested"] = False
            record["control"]["started"] = True
            if auto_continue is not None:
                record["policy"]["auto_continue"] = bool(auto_continue)
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "run.resumed")
            return self.summary(record)

    def stop(self, run_id: str) -> dict[str, Any]:
        """Cancel running workers now and pause. Partial work stays checkpointed."""
        with self._lock:
            record = self.store.load(run_id)
            record["control"]["paused"] = True
            cancelled = self._cancel_active(record, reason="stopped by user")
            record["control"]["stop_requested"] = bool(cancelled["remote"])
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "run.stopped", detail=f"cancelled {cancelled['count']} worker(s)")
            return self.summary(record)

    def decide(self, run_id: str, gate_id: str, approve: bool, note: str | None = None) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            gate = next((item for item in record["gates"] if item["id"] == gate_id), None)
            if gate is None:
                raise OrchestratorError(f"unknown gate {gate_id}")
            if gate["status"] != "open":
                return self.summary(record)
            gate["status"] = "approved" if approve else "rejected"
            gate["decided_at"] = now()
            gate["note"] = redact(note or "", 500) or None
            self._apply_decision(record, gate, approve, gate["note"])
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, f"gate.{gate['status']}", gate.get("node"), f"{gate['kind']}: {gate['reason']}")
            return self.summary(record)

    def retry(self, run_id: str, node_id: str) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            if node_id == "_final":
                record["final"]["repairs"] = 0
                record["final"]["validation"] = None
                record["state_reason"] = None
            else:
                node = self._node(record, node_id)
                if node["state"] in ACTIVE_NODE_STATES:
                    raise OrchestratorError(f"{node_id} is still running")
                if node["state"] == "PASSED":
                    raise OrchestratorError(f"{node_id} already passed; use review-again to re-check it")
                node["state"] = "FAILED_RETRYABLE"
                node["retries"] = 0
                node["selection"] = None
                node["wait_reason"] = "retry requested by user"
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "node.retry", node_id, "retry requested by user")
            return self.summary(record)

    def reassign(self, run_id: str, node_id: str, provider: str, model: str | None = None, effort: str | None = None) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            node = self._node(record, node_id)
            if self.registry().get(provider) is None:
                raise OrchestratorError(f"provider {provider} is not configured")
            record["overrides"]["nodes"][node_id] = _clean_override({"provider": provider, "model": model, "effort": effort})
            node["excluded_providers"] = [item for item in node["excluded_providers"] if item != provider]
            if node["state"] in ACTIVE_NODE_STATES:
                self._cancel_node(record, node, "reassigned by user")
            if node["state"] in {"FAILED_FINAL", "FAILED_RETRYABLE", "CANCELLED", "PENDING", "RUNNABLE"}:
                node["state"] = "FAILED_RETRYABLE" if node["state"] != "PENDING" else "PENDING"
                node["retries"] = 0
                node["selection"] = None
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "node.reassigned", node_id, f"{provider} {model or ''} {effort or ''}".strip())
            return self.summary(record)

    def review_again(self, run_id: str, node_id: str) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            node = self._node(record, node_id)
            if node["role"] not in INTEGRATED_ROLES:
                raise OrchestratorError("only implementation nodes can be reviewed")
            if node["integrated"]:
                raise OrchestratorError(f"{node_id} is already integrated; review the integration branch instead")
            if node["state"] not in {"PASSED", "APPROVAL_REQUIRED"} or not node["worktree"]:
                raise OrchestratorError(f"{node_id} has no validated change to review yet")
            node["state"] = "WAITING_FOR_REVIEW"
            node["review"]["accepted_by_user"] = False
            self._close_node_gates(record, node_id, "superseded by a new review")
            self._create_reviewer(record, node, extra_round=True)
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "node.review_again", node_id)
            return self.summary(record)

    def set_override(
        self,
        run_id: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        effort: str | None = None,
        role: str | None = None,
        node: str | None = None,
        clear: bool = False,
    ) -> dict[str, Any]:
        """Record a user provider/model/effort override in run state only.

        Workflow manifests and task definitions are never modified.
        """
        with self._lock:
            record = self.store.load(run_id)
            value = {} if clear else _clean_override({"provider": provider, "model": model, "effort": effort})
            if provider and self.registry().get(provider) is None:
                raise OrchestratorError(f"provider {provider} is not configured")
            if node:
                self._node(record, node)
                target, key = record["overrides"]["nodes"], node
            elif role:
                target, key = record["overrides"]["roles"], role
            else:
                target, key = record["overrides"], "run"
            if value:
                target[key] = value
            elif key in target and key != "run":
                del target[key]
            else:
                record["overrides"]["run"] = {}
            self.store.save(record)
            self.store.append_event(run_id, "override.set", node, f"{role or node or 'run'} -> {value or 'cleared'}")
            return self.summary(record)

    # ------------------------------------------------------------------
    # Driving
    # ------------------------------------------------------------------

    def step(self, run_id: str, dispatch: bool = True) -> dict[str, Any]:
        """One tick. ``dispatch=False`` only collects running workers."""
        with self._lock:
            record = self.store.load(run_id)
            if record["state"] == "COMPLETE":
                return self.summary(record)
            if record["control"].get("stop_requested"):
                self._cancel_active(record, reason="stopped by user")
                record["control"]["stop_requested"] = False
            passed_before = _count_passed(record)
            try:
                self._poll(record)
                # Without Auto Continue a stage boundary is a stopping point: the
                # tick that sees a stage pass integrates it but launches nothing.
                boundary = not record["policy"]["auto_continue"] and _count_passed(record) > passed_before
                dispatching = dispatch and record["control"]["started"] and not record["control"]["paused"]
                if dispatching and not self._blocked(record):
                    self._integrate(record)
                    self._check_completion(record)
                    if not boundary and not self._open_gates(record) and record["state"] != "COMPLETE":
                        self._dispatch(record)
                self._derive_state(record, after_dispatch=dispatching and not boundary)
            except Exception as exc:
                # Whatever the tick already did (collected results, expanded a
                # plan, launched workers) is real; persist it before failing so
                # state.json never falls behind the event log.
                detail = redact(f"{type(exc).__name__}: {exc}", 400)
                self.store.append_event(run_id, "tick.error", None, detail)
                record["state_reason"] = f"tick error: {detail}"
                self.store.save(record)
                raise
            self.store.save(record)
            return self.summary(record)

    def run_loop(self, run_id: str, *, max_seconds: float | None = None, max_ticks: int | None = None, owner: str = "cli") -> dict[str, Any]:
        """Drive the run. With auto_continue, until a stop state; otherwise to
        the next stage boundary. Only one live process may drive a run."""
        if not self.store.acquire_driver(run_id, owner):
            raise OrchestratorError("another live orchestrator process is already driving this run")
        started = time.monotonic()
        ticks = 0
        try:
            record = self.store.load(run_id)
            if not record["control"]["started"]:
                self.start(run_id)
            passed_before = _count_passed(self.store.load(run_id))
            boundary = False
            while True:
                # Without Auto Continue, reaching a stage boundary stops new
                # dispatch; workers already running are still collected.
                summary = self.step(run_id, dispatch=not boundary)
                ticks += 1
                record = self.store.load(run_id)
                active = _active(record)
                if record["state"] == "COMPLETE":
                    break
                if record["state"] in STOP_STATES and not active:
                    break
                if not record["policy"]["auto_continue"] and _count_passed(record) > passed_before:
                    boundary = True
                    if not active:
                        break
                if max_ticks is not None and ticks >= max_ticks:
                    break
                if max_seconds is not None and time.monotonic() - started >= max_seconds:
                    break
                if active:
                    self._sleep(float(record["policy"]["poll_interval_seconds"]))
            return summary
        finally:
            self.store.release_driver(run_id)

    # ------------------------------------------------------------------
    # Tick internals
    # ------------------------------------------------------------------

    def _poll(self, record: dict[str, Any]) -> None:
        for node_id in list(record["order"]):
            node = record["nodes"][node_id]
            if node["state"] not in ACTIVE_NODE_STATES:
                continue
            key = (record["run_id"], node_id)
            handle = self._handles.get(key)
            if handle is None:
                handle = self._reattach(node)
                if handle is None:
                    process = node.get("process") or {}
                    if process.get("pid") and pid_alive(process.get("pid")):
                        node["wait_reason"] = "worker from an earlier orchestrator process is still running; its outcome will be treated as interrupted"
                        continue
                    self._fail(record, node, "interrupted", "the orchestrator restarted while this worker was running; outcome unknown, partial work kept")
                    continue
                self._handles[key] = handle
                self.store.append_event(record["run_id"], "worker.reattached", node_id, f"pid {handle.pid} via {handle.provider_id}")
            adapter = self._adapter(handle.provider_id)
            status = adapter.poll(handle)
            if status.running:
                elapsed = time.monotonic() - handle.started_monotonic
                if elapsed > int(record["policy"]["worker_timeout_seconds"]):
                    adapter.cancel(handle)
                    self._handles.pop(key, None)
                    self._fail(record, node, "timeout", f"worker exceeded {record['policy']['worker_timeout_seconds']}s")
                continue
            result = adapter.collect(handle)
            self._handles.pop(key, None)
            self._finish_worker(record, node, result)

    def _reattach(self, node: dict[str, Any]) -> RunningAgent | None:
        """Rebuild a handle for a subprocess worker launched by an earlier
        orchestrator process, so its output is collected instead of discarded.

        In-process (synthetic) workers and records without an output path
        cannot be reattached.
        """
        process = node.get("process") or {}
        provider = process.get("provider") or (node.get("selection") or {}).get("provider")
        if not provider or process.get("token") or not process.get("stdout_path"):
            return None
        if self.registry().get(provider) is None:
            return None
        try:
            started = datetime.fromisoformat(str(process.get("started_at")))
            elapsed = max((datetime.now(timezone.utc) - started).total_seconds(), 0.0)
        except (TypeError, ValueError):
            elapsed = 0.0
        return RunningAgent(
            provider_id=provider,
            node_id=node["id"],
            pid=process.get("pid"),
            started_monotonic=time.monotonic() - elapsed,
            started_at=str(process.get("started_at") or now()),
            stdout_path=process["stdout_path"],
            stderr_path=process.get("stderr_path") or process["stdout_path"],
            result_path=process.get("result_path"),
            display=process.get("display") or "",
        )

    def _finish_worker(self, record: dict[str, Any], node: dict[str, Any], result: AgentResult) -> None:
        payload = result.as_dict()
        structured = payload.pop("structured", None)
        node["result"] = {
            "outcome": payload["outcome"],
            "failure_kind": payload["failure_kind"],
            "summary": payload["summary"],
            "self_reported_status": str((structured or {}).get("status") or "")[:40] or None,
            "usage": payload["usage"],
            "duration_ms": payload["duration_ms"],
            "at": now(),
        }
        usage = record["usage"]
        usage["workers"] += 1
        for key in ("input_tokens", "cached_tokens", "output_tokens"):
            usage[key] += int((result.usage or {}).get(key) or 0)
        self.store.append_event(record["run_id"], "worker.finished", node["id"], f"{result.outcome} {result.failure_kind or ''} {result.summary[:160]}")
        if result.outcome != "completed":
            self._record_telemetry(record, node, result, validator_passed=None)
            self._fail(record, node, result.failure_kind or "process_error", result.detail or "worker failed")
            return
        if isinstance(structured, dict) and structured.get("status") == "needs_decision":
            if node["worktree"] and node["role"] in {"implementer", "test_author", "repairer"}:
                self._checkpoint(record, node, "needs decision")
            question = redact(structured.get("question") or structured.get("summary") or "the agent needs a decision", 500)
            node["state"] = "APPROVAL_REQUIRED"
            self._open_gate(record, "agent_needs_decision", question, node["id"])
            self._record_telemetry(record, node, result, validator_passed=None)
            return
        if node["role"] == "planner":
            self._finish_planner(record, node, structured)
        elif node["role"] == "reviewer":
            self._finish_review(record, node, structured)
        else:
            self._finish_edit(record, node, structured)
        self._record_telemetry(record, node, result, validator_passed=(node.get("validation") or {}).get("passed"))

    def _finish_planner(self, record: dict[str, Any], node: dict[str, Any], structured: dict[str, Any] | None) -> None:
        try:
            added, notes = planner.expand(
                record["nodes"],
                node["id"],
                structured,
                record["policy"]["max_planned_tasks"],
                approved_commands=record["policy"]["approved_commands"],
                project_commands=_project_commands(record.get("project")),
            )
        except PlanError as exc:
            self._fail(record, node, "malformed", f"planner output rejected: {exc}")
            return
        for note in notes:
            self.store.append_event(record["run_id"], "plan.adjusted", node["id"], note)
        for node_id in added:
            record["order"].append(node_id)
            planned = record["nodes"][node_id]
            # A planned targeted test runs first; the project's full suite
            # still guards integration.
            planned["validators"] = [*planned["validators"], *record["policy"]["default_validators"]]
        node["state"] = "PASSED"
        node["completed_at"] = now()
        node["validation"] = {"passed": True, "declared_validators": 0, "evidence": [{"name": "plan-structure", "kind": "plan", "passed": True, "detail": f"{len(added)} task(s)"}]}
        self.store.append_event(record["run_id"], "plan.expanded", node["id"], ", ".join(added))

    def _finish_edit(self, record: dict[str, Any], node: dict[str, Any], structured: dict[str, Any] | None) -> None:
        node["state"] = "VALIDATING"
        worktree = node["worktree"]
        self._checkpoint(record, node, f"attempt {node['attempts']}")
        manager = self._manager(record)
        changed = manager.changed_files(worktree["path"], worktree["base_commit"])
        validators = node["validators"] or record["policy"]["default_validators"]
        validation = run_all(
            validators,
            worktree["path"],
            changed=changed,
            scope=node["scope"],
            timeout=int(record["policy"]["worker_timeout_seconds"]),
        )
        validation["changed_files"] = changed[:50]
        validation["at"] = now()
        node["validation"] = validation
        self.store.append_event(record["run_id"], "validation." + ("passed" if validation["passed"] else "failed"), node["id"], _evidence_line(validation))
        if not validation["passed"]:
            self._validation_failed(record, node, validation)
            return
        if node["role"] == "repairer":
            subject = record["nodes"][node["subject"]]
            apply_dispositions(subject["review"]["findings"], structured)
            subject["validation"] = validation
            subject["checkpoint"] = node["checkpoint"]
            node["state"] = "PASSED"
            node["completed_at"] = now()
            self._release_claim(record, node, "repair validated")
            subject["state"] = "WAITING_FOR_REVIEW"
            self._create_reviewer(record, subject)
            return
        if self._review_required(record, node):
            node["state"] = "WAITING_FOR_REVIEW"
            self._create_reviewer(record, node)
            return
        node["state"] = "PASSED"
        node["completed_at"] = now()

    def _validation_failed(self, record: dict[str, Any], node: dict[str, Any], validation: dict[str, Any]) -> None:
        detail = _evidence_line(validation)
        _push_failure(node, "validator_failed", (node.get("selection") or {}).get("provider"), detail)
        policy = record["policy"]
        if node["execution_path"] == "model" and node["escalations"] < policy["max_escalations"]:
            rung = _next_rung(node)
            if rung:
                node["capability_class"] = rung["capability_class"]
                node["effort"] = rung["effort"]
                node["escalations"] += 1
                node["state"] = "FAILED_RETRYABLE"
                node["selection"] = None
                label = f"{rung['capability_class']}/{rung['effort']}"
                node["wait_reason"] = f"validator failed; escalated to {label}"
                self.store.append_event(record["run_id"], "node.escalated", node["id"], f"-> {label}: {detail}")
                return
        node["retries"] += 1
        if node["retries"] <= policy["max_stage_retries"] and node["execution_path"] == "deterministic":
            node["state"] = "FAILED_RETRYABLE"
            node["wait_reason"] = "validator failed; retrying"
            return
        node["state"] = "FAILED_FINAL"
        node["wait_reason"] = f"validator still failing after {node['escalations']} escalation(s): {detail}"
        if node["role"] == "repairer" and node.get("subject") in record["nodes"]:
            subject = record["nodes"][node["subject"]]
            subject["state"] = "FAILED_FINAL"
            subject["wait_reason"] = f"repair {node['id']} could not pass validation"
        self.store.append_event(record["run_id"], "node.failed", node["id"], node["wait_reason"])

    def _finish_review(self, record: dict[str, Any], reviewer: dict[str, Any], structured: dict[str, Any] | None) -> None:
        subject = record["nodes"][reviewer["subject"]]
        round_number = subject["review"]["rounds"]
        provider = (reviewer.get("selection") or {}).get("provider") or "unknown"
        try:
            parsed = parse_review(structured, round_number, provider)
        except MalformedReview as exc:
            self._fail(record, reviewer, "malformed", f"review rejected: {exc}")
            return
        reviewer["state"] = "PASSED"
        reviewer["completed_at"] = now()
        reviewer["validation"] = {"passed": True, "declared_validators": 0, "evidence": [{"name": "review-structure", "kind": "review", "passed": True, "detail": f"{parsed['verdict']}, {len(parsed['findings'])} finding(s)"}]}
        author = (subject.get("selection") or {}).get("provider")
        subject["review"]["findings"].extend(parsed["findings"])
        subject["review"]["reviewers"].append(
            {
                "node": reviewer["id"],
                "round": round_number,
                "provider": provider,
                "model": (reviewer.get("selection") or {}).get("model"),
                "independent_provider": bool(author and provider != author),
                "verdict": parsed["verdict"],
                "findings": len(parsed["findings"]),
            }
        )
        this_round = [item for item in subject["review"]["findings"] if item["round"] == round_number]
        blocking = material(this_round, record["policy"]["material_severities"])
        self.store.append_event(record["run_id"], "review.completed", subject["id"], f"{parsed['verdict']}; {len(blocking)} material finding(s)")
        if not blocking and parsed["verdict"] != "blocked":
            subject["state"] = "PASSED"
            subject["completed_at"] = now()
            return
        if subject["review"]["rounds"] < record["policy"]["max_review_rounds"]:
            subject["state"] = "NEEDS_REPAIR"
            self._create_repair(record, subject, blocking)
            return
        subject["state"] = "APPROVAL_REQUIRED"
        self._open_gate(
            record,
            "unresolved_review_findings",
            f"{len(blocking)} material finding(s) remain after {subject['review']['rounds']} review round(s)",
            subject["id"],
        )

    def _create_reviewer(self, record: dict[str, Any], subject: dict[str, Any], extra_round: bool = False) -> None:
        subject["review"]["rounds"] += 1
        round_number = subject["review"]["rounds"]
        reviewer_id = f"{subject['id']}.review{round_number}"
        capability = subject["requested_capability_class"]
        if capability in {"deterministic", "fast"}:
            capability = "balanced"
        reviewer = new_node(
            reviewer_id,
            f"Independently review {subject['id']}: {subject['goal']}",
            "reviewer",
            capability_class=capability,
            effort="medium",
            subject=subject["id"],
            origin="review",
            context_budget=1200,
        )
        record["nodes"][reviewer_id] = reviewer
        _insert_after(record["order"], subject["id"], reviewer_id)
        self.store.append_event(record["run_id"], "review.requested", subject["id"], f"round {round_number}" + (" (user requested)" if extra_round else ""))

    def _create_repair(self, record: dict[str, Any], subject: dict[str, Any], findings: list[dict[str, Any]]) -> None:
        round_number = subject["review"]["rounds"]
        repair_id = f"{subject['id']}.repair{round_number}"
        capability, effort = _repair_class(subject, findings)
        repair = new_node(
            repair_id,
            f"Repair review findings on {subject['id']}: {subject['goal']}",
            "repairer",
            scope=subject["scope"],
            capability_class=capability,
            effort=effort,
            validators=subject["validators"],
            subject=subject["id"],
            origin="repair",
        )
        repair["worktree"] = dict(subject["worktree"], owned_by=repair_id)
        repair["finding_ids"] = [item["id"] for item in findings]
        record["nodes"][repair_id] = repair
        _insert_after(record["order"], f"{subject['id']}.review{round_number}", repair_id)
        self.store.append_event(record["run_id"], "repair.requested", subject["id"], f"{len(findings)} material finding(s) -> {repair_id}")

    def _review_required(self, record: dict[str, Any], node: dict[str, Any]) -> bool:
        if node["review_required"] is not None:
            return bool(node["review_required"])
        return bool(record["policy"]["require_independent_review_for_model_edits"] and node["execution_path"] == "model")

    # -- failures -----------------------------------------------------------

    def _fail(self, record: dict[str, Any], node: dict[str, Any], kind: str, detail: str) -> None:
        provider = (node.get("selection") or {}).get("provider")
        _push_failure(node, kind, provider, detail)
        if node["worktree"] and node["role"] in {"implementer", "test_author", "repairer"}:
            try:
                self._checkpoint(record, node, f"partial after {kind}")
            except GitError:
                pass
        self.store.append_event(record["run_id"], f"node.{kind}", node["id"], detail)
        if kind == "cancelled":
            node["state"] = "FAILED_RETRYABLE"
            node["selection"] = None
            node["wait_reason"] = "cancelled; will resume when the run resumes"
            return
        policy = record["policy"]
        if provider and policy["provider_failover"]:
            same_kind = [item for item in node["failures"] if item["provider"] == provider and item["kind"] in {"process_error", "timeout", "interrupted", "malformed"}]
            if kind in PROVIDER_FAILURES or len(same_kind) >= 2:
                if provider not in node["excluded_providers"]:
                    node["excluded_providers"].append(provider)
                    self.store.append_event(record["run_id"], "provider.failover", node["id"], f"{provider} excluded for this node after {kind}")
        node["retries"] += 1
        if node["retries"] > policy["max_stage_retries"]:
            node["state"] = "FAILED_FINAL"
            node["wait_reason"] = f"{kind} after {node['retries'] - 1} retr(ies): {redact(detail, 200)}"
            return
        node["state"] = "FAILED_RETRYABLE"
        node["selection"] = None
        node["wait_reason"] = f"{kind}; retry {node['retries']}/{policy['max_stage_retries']} will re-route"

    def _checkpoint(self, record: dict[str, Any], node: dict[str, Any], label: str) -> None:
        worktree = node["worktree"]
        if not worktree:
            return
        commit = self._manager(record).checkpoint(worktree["path"], f"agent-os {record['run_id']}/{node['id']}: {label}")
        node["checkpoint"] = {"commit": commit or head_commit(worktree["path"]), "label": label, "at": now()}
        if node["role"] == "repairer" and node.get("subject") in record["nodes"]:
            record["nodes"][node["subject"]]["checkpoint"] = node["checkpoint"]

    # -- dispatch -------------------------------------------------------------

    def _dispatch(self, record: dict[str, Any]) -> None:
        policy = record["policy"]
        nodes = record["nodes"]
        running: dict[str, int] = {}
        editors = 0
        for node in nodes.values():
            if node["state"] in ACTIVE_NODE_STATES:
                selection = node.get("selection") or {}
                if selection.get("provider"):
                    _count_running(running, selection["provider"], selection.get("capability_class"))
                if node["role"] in {"implementer", "test_author", "repairer"}:
                    editors += 1
        for node_id in list(record["order"]):
            node = nodes[node_id]
            if node["state"] not in DISPATCHABLE_NODE_STATES:
                continue
            unmet = [dep for dep in node["depends_on"] if not _dependency_met(nodes.get(dep))]
            if unmet:
                node["wait_reason"] = "waiting for " + ", ".join(unmet)
                continue
            if node["approval_gate"] and not node["approval"]:
                if node["approval_gate"]["kind"] in policy["approval_gates"]:
                    node["state"] = "APPROVAL_REQUIRED"
                    self._open_gate(record, node["approval_gate"]["kind"], node["approval_gate"].get("reason") or node["goal"], node_id)
                    return
                node["approval"] = {"decision": "auto", "at": now(), "note": "gate kind not listed in run policy"}
            editing = node["role"] in {"implementer", "test_author", "repairer"}
            if editing:
                if editors >= policy["max_parallel_editors"]:
                    node["state"] = "RUNNABLE"
                    node["wait_reason"] = f"max_parallel_editors={policy['max_parallel_editors']} reached"
                    continue
                blockers = self._scope_blockers(record, node)
                if blockers:
                    node["state"] = "RUNNABLE"
                    node["wait_reason"] = "serialized: editable scope overlaps " + ", ".join(blockers)
                    continue
            if node["execution_path"] == "model" and record["launches"] >= record["launch_budget"]:
                self._open_gate(record, "budget_exhausted", f"launch budget of {record['launch_budget']} worker(s) is used up", None)
                return
            launched = self._launch(record, node, running)
            if launched and editing:
                editors += 1

    def _scope_blockers(self, record: dict[str, Any], node: dict[str, Any]) -> list[str]:
        blockers = []
        for other in record["nodes"].values():
            if other["id"] == node["id"] or other["id"] == node.get("subject") or other.get("subject") == node["id"]:
                continue
            if other["role"] not in {"implementer", "test_author"}:
                continue
            holds = other["worktree"] is not None and not other["integrated"] and other["state"] not in {"CANCELLED"}
            if holds and scopes_overlap(node["scope"], other["scope"]):
                blockers.append(other["id"])
        return blockers

    def _launch(self, record: dict[str, Any], node: dict[str, Any], running: dict[str, int]) -> bool:
        policy = record["policy"]
        editing = node["role"] in {"implementer", "test_author", "repairer"}
        manager = self._manager(record)
        integration = self._ensure_integration(record)
        if editing and node["worktree"] is None:
            generation = int(node.get("generation", 0))
            try:
                created = manager.create(node["id"], integration["head"], generation)
            except GitError as exc:
                self._fail(record, node, "process_error", f"worktree creation failed: {exc}")
                return False
            node["worktree"] = dict(created, owned_by=node["id"])
            node["state"] = "CLAIMED"
            self.store.append_event(record["run_id"], "worktree.created", node["id"], node["worktree"]["branch"])
        if node["execution_path"] == "deterministic":
            return self._run_deterministic(record, node)
        subject = record["nodes"].get(node.get("subject") or "")
        avoid = []
        if node["role"] == "reviewer" and subject and subject.get("selection"):
            avoid = [subject["selection"]["provider"]]
        selection = select(
            self.registry(),
            capability_class=node["capability_class"],
            effort=node["effort"],
            role=node["role"],
            preference=policy["preference"],
            availability=self.availability(),
            excluded=node["excluded_providers"],
            avoid=avoid,
            running=running,
            override=self._override_for(record, node),
            require_avoid=node["role"] == "reviewer" and policy["require_distinct_review_provider"],
        )
        if not selection.get("resolved"):
            if selection.get("waiting"):
                node["state"] = "RUNNABLE"
                node["wait_reason"] = selection["reason"]
                return False
            node["state"] = "FAILED_FINAL"
            node["wait_reason"] = f"no provider: {selection['reason']}"
            self.store.append_event(record["run_id"], "node.unroutable", node["id"], selection["reason"])
            return False
        selection["at"] = now()
        node["selection"] = selection
        if node["role"] == "reviewer":
            cwd = subject["worktree"]["path"]
        elif node["role"] == "planner":
            cwd = integration["path"]
        else:
            cwd = node["worktree"]["path"]
        attempt = node["attempts"] + 1
        worker_dir = self.store.worker_dir(record["run_id"], node["id"], attempt)
        diff = None
        findings = None
        if node["role"] == "reviewer":
            diff = manager.diff(cwd, subject["worktree"]["base_commit"])
        if node["role"] == "repairer" and subject:
            wanted = set(node.get("finding_ids") or [])
            findings = [item for item in subject["review"]["findings"] if item["id"] in wanted]
        prompt = prompts.build(record, node, diff=diff, findings=findings)
        prompt += _prior_attempts(node)
        prompt_path = worker_dir / "prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        provider = self.registry().get(selection["provider"]) or {}
        request = AgentLaunchRequest(
            run_id=record["run_id"],
            node_id=node["id"],
            role=node["role"],
            cwd=str(cwd),
            prompt_path=str(prompt_path),
            output_dir=str(worker_dir),
            capability_class=selection["capability_class"],
            effort=selection["effort"],
            model=selection["model"],
            provider_effort=selection["provider_effort"],
            read_only=node["role"] in {"reviewer", "planner"},
            timeout_seconds=int(policy["worker_timeout_seconds"]),
            allowed_tools=list((provider.get("options") or {}).get("allowed_tools") or []),
        )
        node["state"] = "LAUNCHING"
        node["attempts"] = attempt
        try:
            handle = self._adapter(selection["provider"]).start(request)
        except Exception as exc:
            kind = "unavailable" if isinstance(exc, (FileNotFoundError, RuntimeError)) else "process_error"
            self._fail(record, node, kind, f"launch failed: {exc}")
            return False
        self._handles[(record["run_id"], node["id"])] = handle
        node["process"] = handle.persisted()
        node["state"] = "RUNNING"
        node["wait_reason"] = None
        record["launches"] += 1
        _count_running(running, selection["provider"], selection["capability_class"])
        self._announce(record, node)
        self.store.append_event(
            record["run_id"],
            "worker.launched",
            node["id"],
            f"{node['role']} via {selection['provider']} model={selection['model']} effort={selection['provider_effort']} ({selection['reason']})",
        )
        return True

    def _run_deterministic(self, record: dict[str, Any], node: dict[str, Any]) -> bool:
        from .validators import run_validator

        node["attempts"] += 1
        node["state"] = "RUNNING"
        cwd = node["worktree"]["path"] if node["worktree"] else self._ensure_integration(record)["path"]
        outcome = run_validator({"kind": "command", "command": node["command"], "name": "deterministic-step"}, cwd, int(record["policy"]["worker_timeout_seconds"]))
        self.store.append_event(record["run_id"], "deterministic.ran", node["id"], outcome.get("detail"))
        node["selection"] = {"resolved": True, "provider": None, "model": None, "capability_class": "deterministic", "effort": "none", "provider_effort": None, "reason": "deterministic execution path", "overridden": False, "notes": [], "at": now()}
        result = AgentResult(
            outcome="completed" if outcome["passed"] else "failed",
            failure_kind=None if outcome["passed"] else "process_error",
            summary=f"deterministic command exited {outcome.get('returncode')}",
            structured={"status": "done"},
            detail=outcome.get("detail"),
        )
        self._finish_worker(record, node, result)
        return True

    # -- integration ------------------------------------------------------------

    def _integrate(self, record: dict[str, Any]) -> None:
        manager = None
        for node_id in list(record["order"]):
            node = record["nodes"][node_id]
            if node["role"] not in INTEGRATED_ROLES or node["state"] != "PASSED" or node["integrated"]:
                continue
            refusal = self._integration_refusal(record, node)
            if refusal == "gate":
                continue
            if refusal:
                node["state"] = "FAILED_FINAL"
                node["wait_reason"] = f"integration refused: {refusal}"
                self.store.append_event(record["run_id"], "integration.refused", node_id, refusal)
                continue
            manager = manager or self._manager(record)
            self._ensure_integration(record)
            outcome = manager.merge(node["worktree"]["branch"], f"agent-os {record['run_id']}: integrate {node_id}")
            if outcome["merged"]:
                node["integrated"] = True
                node["integration"] = {"commit": outcome["commit"], "at": now()}
                record["integration"]["head"] = outcome["commit"]
                record["integration"]["merged"].append(node_id)
                self._release_claim(record, node, "integrated")
                self.store.append_event(record["run_id"], "integration.merged", node_id, outcome["commit"][:12])
                if record["policy"]["cleanup_worktrees"]:
                    cleanup = manager.remove(node["worktree"]["path"], node["worktree"]["branch"])
                    node["worktree"]["removed"] = cleanup["removed"]
                    node["worktree"]["branch_deleted"] = cleanup["branch_deleted"]
            else:
                node["state"] = "APPROVAL_REQUIRED"
                node["integration"] = {"conflicts": outcome["conflicts"], "at": now()}
                self._open_gate(
                    record,
                    "semantic_merge_conflict",
                    "merge conflict in " + (", ".join(outcome["conflicts"][:8]) or "unknown files")
                    + "; approve to redo this node on top of the current integration branch, reject to stop",
                    node_id,
                )

    def _integration_refusal(self, record: dict[str, Any], node: dict[str, Any]) -> str | None:
        validation = node.get("validation") or {}
        if not validation.get("passed"):
            return "no passing validator evidence"
        if self._review_required(record, node):
            reviewers = node["review"]["reviewers"]
            clean = reviewers and reviewers[-1]["verdict"] != "blocked" and not material(
                [item for item in node["review"]["findings"] if item["round"] == reviewers[-1]["round"]],
                record["policy"]["material_severities"],
            )
            if not (clean or node["review"]["accepted_by_user"]):
                return "required independent review has not approved this change"
        if (
            record["policy"]["validation_required_before_integration"]
            and not validation.get("declared_validators")
            and not node.get("allow_unvalidated")
        ):
            if not self._node_gate(record, node["id"], "policy_restricted_action"):
                node["state"] = "APPROVAL_REQUIRED"
                self._open_gate(
                    record,
                    "policy_restricted_action",
                    "no declared validator ran for this change; approve to integrate it without test evidence",
                    node["id"],
                )
            return "gate"
        return None

    def _ensure_integration(self, record: dict[str, Any]) -> dict[str, Any]:
        integration = record["integration"]
        manager = self._manager(record)
        if not integration["path"] or not manager.is_registered(integration["path"]):
            created = manager.ensure_integration(integration.get("head") or record["base_commit"])
            integration["branch"] = created["branch"]
            integration["path"] = created["path"]
        integration["head"] = manager.integration_head()
        return integration

    def _check_completion(self, record: dict[str, Any]) -> None:
        if record["final"]["validation"] and record["final"]["validation"]["passed"]:
            return
        nodes = record["nodes"].values()
        if any(node["state"] != "PASSED" for node in nodes):
            return
        if any(node["role"] in INTEGRATED_ROLES and not node["integrated"] for node in nodes):
            return
        if _active(record) or self._open_gates(record):
            return
        integration = self._ensure_integration(record)
        validators = record["policy"]["completion_validators"] or record["policy"]["default_validators"]
        validation = run_all(validators, integration["path"], timeout=int(record["policy"]["worker_timeout_seconds"]))
        validation["at"] = now()
        validation["commit"] = integration["head"]
        record["final"]["validation"] = validation
        self.store.append_event(record["run_id"], "completion." + ("passed" if validation["passed"] else "failed"), None, _evidence_line(validation))
        if validation["passed"]:
            if record["policy"]["final_integration"] == "merge_to_base" and record["integration"]["merged"]:
                self._open_gate(
                    record,
                    "consequential_repository_write",
                    f"land {integration['branch']} onto {record['base_ref'] or record['base_commit'][:12]}",
                    None,
                )
                return
            self._finish(record)
            return
        if record["final"]["repairs"] < record["policy"]["max_final_repairs"]:
            record["final"]["repairs"] += 1
            fix_id = f"final-fix{record['final']['repairs']}"
            fix = new_node(
                fix_id,
                "Make the integrated result pass the completion validators: " + _evidence_line(validation),
                "implementer",
                capability_class="reasoning",
                effort="high",
                validators=validators,
                origin="completion",
            )
            record["nodes"][fix_id] = fix
            record["order"].append(fix_id)
            record["final"]["validation"] = None
            self.store.append_event(record["run_id"], "completion.repair", fix_id, "completion validators failed; scheduled a bounded fix")
            return
        record["state_reason"] = "completion validators failed and the final repair budget is used up"

    def _finish(self, record: dict[str, Any]) -> None:
        integration = record["integration"]
        merged = integration["merged"]
        record["final"]["summary"] = {
            "integration_branch": integration["branch"],
            "integration_commit": integration["head"],
            "base_ref": record["base_ref"],
            "base_commit": record["base_commit"],
            "integrated_nodes": merged,
            "how_to_land": (
                f"git merge --ff-only {integration['branch']}" if merged else "nothing to land: no changes were integrated"
            ),
        }
        record["state"] = "COMPLETE"
        record["state_reason"] = "all stages validated, reviewed and integrated; completion validators passed"
        if record["policy"]["cleanup_worktrees"] and integration["path"]:
            self._manager(record).remove(integration["path"], None)
        self.store.append_event(record["run_id"], "run.complete", None, record["final"]["summary"]["how_to_land"])

    def _land(self, record: dict[str, Any]) -> None:
        """Fast-forward the base branch to the validated integration branch."""
        from .worktrees import git

        repo = Path(record["repository"])
        branch = record["integration"]["branch"]
        base = record["base_ref"]
        if not base:
            record["final"]["landed"] = {"ok": False, "reason": "the run started from a detached HEAD"}
            return
        manager = self._manager(record)
        base_head = git(["rev-parse", base], repo).stdout.strip()
        if not manager.is_ancestor(base_head, branch):
            record["final"]["landed"] = {"ok": False, "reason": f"{base} moved since the run started; merge {branch} manually"}
            return
        if current_branch(repo) == base:
            if is_dirty(repo):
                record["final"]["landed"] = {"ok": False, "reason": f"{base} is checked out with uncommitted changes"}
                return
            git(["merge", "--ff-only", branch], repo)
        else:
            git(["update-ref", f"refs/heads/{base}", git(["rev-parse", branch], repo).stdout.strip(), base_head], repo)
        record["final"]["landed"] = {"ok": True, "commit": git(["rev-parse", base], repo).stdout.strip(), "at": now()}

    # -- gates ----------------------------------------------------------------

    def _open_gate(self, record: dict[str, Any], kind: str, reason: str, node_id: str | None) -> dict[str, Any]:
        for gate in record["gates"]:
            if gate["status"] == "open" and gate["kind"] == kind and gate.get("node") == node_id:
                return gate
        gate = {
            "id": f"G{len(record['gates']) + 1}",
            "kind": kind,
            "reason": redact(reason, 500),
            "node": node_id,
            "status": "open",
            "created_at": now(),
            "decided_at": None,
            "note": None,
        }
        record["gates"].append(gate)
        self.store.append_event(record["run_id"], "gate.opened", node_id, f"{gate['id']} {kind}: {gate['reason']}")
        return gate

    def _open_gates(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        return [gate for gate in record["gates"] if gate["status"] == "open"]

    def _node_gate(self, record: dict[str, Any], node_id: str, kind: str) -> dict[str, Any] | None:
        for gate in reversed(record["gates"]):
            if gate.get("node") == node_id and gate["kind"] == kind:
                return gate
        return None

    def _close_node_gates(self, record: dict[str, Any], node_id: str, note: str) -> None:
        for gate in record["gates"]:
            if gate.get("node") == node_id and gate["status"] == "open":
                gate["status"] = "superseded"
                gate["decided_at"] = now()
                gate["note"] = note

    def _apply_decision(self, record: dict[str, Any], gate: dict[str, Any], approve: bool, note: str | None) -> None:
        kind = gate["kind"]
        node = record["nodes"].get(gate.get("node") or "")
        if kind == "budget_exhausted":
            if approve:
                record["launch_budget"] += max(record["policy"]["max_launches"] // 2, 5)
            else:
                record["state_reason"] = "launch budget exhausted; user declined more"
            return
        if kind == "consequential_repository_write":
            if approve:
                try:
                    self._land(record)
                except GitError as exc:
                    record["final"]["landed"] = {"ok": False, "reason": redact(exc, 300)}
            else:
                record["final"]["landed"] = {"ok": False, "reason": "user declined to land; the integration branch is kept"}
            self._finish(record)
            return
        if node is None:
            return
        if not approve:
            node["state"] = "CANCELLED" if kind not in {"unresolved_review_findings", "semantic_merge_conflict"} else "FAILED_FINAL"
            node["wait_reason"] = f"{kind} rejected by user" + (f": {note}" if note else "")
            self._release_claim(record, node, "rejected at approval gate")
            return
        if kind == "unresolved_review_findings":
            for finding in node["review"]["findings"]:
                if finding["disposition"] == "open":
                    finding["disposition"] = "accepted"
                    finding["disposition_reason"] = note or "accepted by user at approval gate"
            node["review"]["accepted_by_user"] = True
            node["state"] = "PASSED"
            node["completed_at"] = now()
        elif kind == "semantic_merge_conflict":
            old = node["worktree"]
            node.setdefault("previous_worktrees", []).append({"branch": old["branch"], "path": old["path"], "reason": "merge conflict"})
            node["generation"] = int(node.get("generation", 0)) + 1
            node["worktree"] = None
            node["integration"] = None
            node["review"]["rounds"] = 0
            node["validation"] = None
            _push_failure(node, "merge_conflict", (node.get("selection") or {}).get("provider"), gate["reason"])
            node["state"] = "FAILED_RETRYABLE"
            node["selection"] = None
            node["retries"] = 0
            for other_id in list(record["order"]):
                other = record["nodes"][other_id]
                if other.get("subject") == node["id"] and other["state"] in DISPATCHABLE_NODE_STATES:
                    other["state"] = "CANCELLED"
        elif kind == "agent_needs_decision":
            node.setdefault("decisions", []).append(note or "approved without further instruction")
            node["state"] = "FAILED_RETRYABLE"
            node["selection"] = None
        elif kind == "policy_restricted_action" and node["state"] == "APPROVAL_REQUIRED" and node.get("validation"):
            node["allow_unvalidated"] = True
            node["state"] = "PASSED"
        else:
            node["approval"] = {"decision": "approved", "at": now(), "note": note}
            node["state"] = "RUNNABLE"

    # -- cancellation -------------------------------------------------------------

    def _cancel_active(self, record: dict[str, Any], reason: str) -> dict[str, int]:
        count = 0
        remote = 0
        for node in record["nodes"].values():
            if node["state"] in ACTIVE_NODE_STATES:
                if self._cancel_node(record, node, reason):
                    count += 1
                else:
                    remote += 1
        return {"count": count, "remote": remote}

    def _cancel_node(self, record: dict[str, Any], node: dict[str, Any], reason: str) -> bool:
        key = (record["run_id"], node["id"])
        handle = self._handles.pop(key, None)
        if handle is not None:
            adapter = self._adapter(handle.provider_id)
            adapter.cancel(handle)
            self._fail(record, node, "cancelled", reason)
            return True
        process = node.get("process") or {}
        if process.get("pid") and pid_alive(process["pid"]):
            # Driven by another live orchestrator process: ask it to stop.
            owner = self.store.driver(record["run_id"])
            if owner.get("active") and owner.get("pid") != os.getpid():
                return False
            kill_tree(int(process["pid"]))
        self._fail(record, node, "cancelled", reason)
        return True

    # -- helpers ------------------------------------------------------------------

    def _manager(self, record: dict[str, Any]) -> WorktreeManager:
        layout = record.get("worktree_layout", "legacy")
        return WorktreeManager(record["repository"], self.store.worktree_root(layout), record["run_id"], layout)

    def _node(self, record: dict[str, Any], node_id: str) -> dict[str, Any]:
        node = record["nodes"].get(node_id)
        if node is None:
            raise OrchestratorError(f"unknown node {node_id}")
        return node

    def _override_for(self, record: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
        overrides = record["overrides"]
        merged: dict[str, Any] = {}
        for layer in (overrides.get("run") or {}, (overrides.get("roles") or {}).get(node["role"]) or {}, (overrides.get("nodes") or {}).get(node["id"]) or {}):
            merged.update({key: value for key, value in layer.items() if value})
        return merged

    def _blocked(self, record: dict[str, Any]) -> bool:
        return any(node["state"] in {"FAILED_FINAL", "CANCELLED"} for node in record["nodes"].values())

    def _announce(self, record: dict[str, Any], node: dict[str, Any]) -> None:
        if not record["policy"]["announce_claims"] or not record.get("project") or node["role"] not in {"implementer", "test_author", "repairer"}:
            return
        if node.get("claim_id"):
            return
        try:
            from ..coordination import claim

            outcome = claim(
                record["project"],
                f"orchestrated {record['run_id']}/{node['id']}: {node['goal'][:80]}",
                f"agent-os/{node['selection']['provider']}",
                node["scope"] or ["."],
                lease_minutes=max(int(record["policy"]["worker_timeout_seconds"]) // 60, 30),
                path=self._claims_path,
            )
            node["claim_id"] = outcome["claim"]["claim_id"]
        except Exception:
            node["claim_id"] = None

    def _release_claim(self, record: dict[str, Any], node: dict[str, Any], note: str) -> None:
        claim_id = node.get("claim_id")
        if not claim_id:
            return
        try:
            from ..coordination import release

            release(claim_id, note, path=self._claims_path)
        except Exception:
            pass
        node["claim_id"] = None

    def _record_telemetry(self, record: dict[str, Any], node: dict[str, Any], result: AgentResult, validator_passed: bool | None) -> None:
        if not record["policy"]["telemetry"]:
            return
        selection = node.get("selection") or {}
        try:
            store = self._telemetry or LocalTelemetryStore()
            store.record(
                TelemetryEvent(
                    project_id=_label(record.get("project")) or "unregistered",
                    task_category=_label(f"orchestrator-{node['role']}") or "orchestrator",
                    capability_class=selection.get("capability_class"),
                    execution_path="deterministic" if node["execution_path"] == "deterministic" else "model",
                    provider=_label(selection.get("provider")),
                    model=_label(selection.get("model")),
                    input_tokens=(result.usage or {}).get("input_tokens"),
                    cached_tokens=(result.usage or {}).get("cached_tokens"),
                    output_tokens=(result.usage or {}).get("output_tokens"),
                    duration_ms=result.duration_ms,
                    retries=node["retries"],
                    validator_passed=validator_passed,
                    escalations=node["escalations"],
                    correction_or_override=bool(selection.get("overridden")),
                )
            )
        except (TelemetryPrivacyError, OSError, ValueError):
            pass

    def _derive_state(self, record: dict[str, Any], after_dispatch: bool = False) -> None:
        if record["state"] == "COMPLETE":
            return
        nodes = list(record["nodes"].values())
        active = [node for node in nodes if node["state"] in ACTIVE_NODE_STATES]
        failed = [node for node in nodes if node["state"] in {"FAILED_FINAL", "CANCELLED"}]
        gates = self._open_gates(record)
        if not record["control"]["started"]:
            state, reason = "CREATED", "not started"
        elif record["control"]["paused"]:
            state, reason = "PAUSED", f"paused; {len(active)} worker(s) still finishing" if active else "paused"
        elif failed:
            state, reason = "BLOCKED", "; ".join(f"{node['id']}: {node['wait_reason']}" for node in failed)[:600]
        elif gates:
            state, reason = "APPROVAL_REQUIRED", "; ".join(f"{gate['id']} {gate['kind']}" for gate in gates)
        elif record.get("state_reason") and "completion validators failed" in record["state_reason"]:
            state, reason = "BLOCKED", record["state_reason"]
        elif any(node["role"] == "planner" for node in active):
            state, reason = "PLANNING", None
        elif active and all(node["role"] == "reviewer" for node in active):
            state, reason = "REVIEWING", None
        elif active:
            state, reason = "RUNNING", f"{len(active)} worker(s) running"
        else:
            waiting = [node for node in nodes if node["state"] in DISPATCHABLE_NODE_STATES]
            # Only a tick that actually tried to dispatch can conclude that
            # nothing is runnable; a freshly started run is merely READY.
            if after_dispatch and waiting and not any(node["state"] in {"WAITING_FOR_REVIEW", "NEEDS_REPAIR"} for node in nodes):
                state, reason = "BLOCKED", "no runnable work: " + "; ".join(f"{node['id']}: {node['wait_reason']}" for node in waiting)[:600]
            elif any(node["state"] == "PASSED" and node["role"] in INTEGRATED_ROLES and not node["integrated"] for node in nodes):
                state, reason = "INTEGRATING", None
            else:
                state, reason = "READY", None
        if state != record["state"]:
            self.store.append_event(record["run_id"], "run.state", None, f"{record['state']} -> {state}")
        record["state"] = state
        record["state_reason"] = reason

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------

    def summary(self, record: dict[str, Any]) -> dict[str, Any]:
        nodes = record["nodes"]
        total = len(nodes)
        passed = sum(1 for node in nodes.values() if node["state"] == "PASSED")
        return {
            "run_id": record["run_id"],
            "goal": record["goal"],
            "project": record.get("project"),
            "repository": record["repository"],
            "base_ref": record["base_ref"],
            "base_commit": record["base_commit"],
            "state": record["state"],
            "state_reason": record.get("state_reason"),
            "auto_continue": record["policy"]["auto_continue"],
            "preference": record["policy"]["preference"],
            "paused": record["control"]["paused"],
            "driver": self.store.driver(record["run_id"]),
            "progress": {"passed": passed, "total": total, "integrated": len(record["integration"]["merged"])},
            "launches": record["launches"],
            "launch_budget": record["launch_budget"],
            "usage": record["usage"],
            "preflight": record["preflight"],
            "overrides": record["overrides"],
            "integration": record["integration"],
            "final": record["final"],
            "gates": record["gates"],
            "nodes": [_node_view(nodes[node_id]) for node_id in record["order"]],
        }

    def status(self, run_id: str) -> dict[str, Any]:
        return self.summary(self.store.load(run_id))

    def result(self, run_id: str) -> dict[str, Any]:
        record = self.store.load(run_id)
        findings = []
        for node in record["nodes"].values():
            for finding in node["review"]["findings"]:
                findings.append({"node": node["id"], **finding})
        return {
            "run_id": run_id,
            "state": record["state"],
            "state_reason": record.get("state_reason"),
            "goal": record["goal"],
            "final": record["final"],
            "integration": record["integration"],
            "nodes": [
                {
                    "id": node["id"],
                    "role": node["role"],
                    "state": node["state"],
                    "provider": (node.get("selection") or {}).get("provider"),
                    "model": (node.get("selection") or {}).get("model"),
                    "effort": (node.get("selection") or {}).get("provider_effort"),
                    "capability_class": node["capability_class"],
                    "attempts": node["attempts"],
                    "escalations": node["escalations"],
                    "validated": bool((node.get("validation") or {}).get("passed")),
                    "integrated": node["integrated"],
                }
                for node in (record["nodes"][node_id] for node_id in record["order"])
            ],
            "findings": findings,
            "usage": record["usage"],
            "gates": record["gates"],
        }

    def list_runs(self) -> list[dict[str, Any]]:
        return self.store.list_runs()

    def events(self, run_id: str, after_seq: int = 0, limit: int = 200) -> list[dict[str, Any]]:
        return self.store.read_events(run_id, after_seq, limit)


# ----------------------------------------------------------------------
# Module helpers
# ----------------------------------------------------------------------


def _clean_override(value: dict[str, Any] | None) -> dict[str, Any]:
    return {key: str(item) for key, item in (value or {}).items() if key in {"provider", "model", "effort"} and item}


def _clean_overrides(value: dict[str, Any] | None) -> dict[str, Any]:
    value = value or {}
    return {
        "run": _clean_override(value.get("run")),
        "roles": {str(key): _clean_override(item) for key, item in (value.get("roles") or {}).items()},
        "nodes": {str(key): _clean_override(item) for key, item in (value.get("nodes") or {}).items()},
    }


def _project_validators(project_id: str) -> list[dict[str, Any]]:
    """Default validators from the project's canonical ``validation_commands``."""
    try:
        from ..registry import get_project, load_state

        commands = load_state(get_project(project_id)).get("validation_commands") or []
    except Exception:
        return []
    return [{"kind": "command", "command": str(command), "name": f"project-validation-{index + 1}"} for index, command in enumerate(commands) if str(command).strip()]


def _project_commands(project_id: str | None) -> list[str]:
    return [validator["command"] for validator in _project_validators(project_id)] if project_id else []


def _count_running(running: dict[str, int], provider: str, capability_class: str | None) -> None:
    running[provider] = running.get(provider, 0) + 1
    if capability_class:
        key = load_key(provider, capability_class)
        running[key] = running.get(key, 0) + 1


def _next_rung(node: dict[str, Any]) -> dict[str, str] | None:
    """The next step on the node's escalation ladder (cheapest-first)."""
    ladder = node.get("ladder")
    if ladder is None:  # records created before ladders existed
        promoted = next_class(node["capability_class"])
        return {"capability_class": promoted, "effort": node["effort"]} if promoted else None
    step = int(node.get("ladder_step", 0)) + 1
    if step >= len(ladder):
        return None
    node["ladder_step"] = step
    return ladder[step]


def _repair_class(subject: dict[str, Any], findings: list[dict[str, Any]]) -> tuple[str, str]:
    """Downgrade repairs of minor findings to the class the task was planned
    at; serious findings keep whatever class the task escalated to."""
    serious = any(item["severity"] in {"critical", "high"} for item in findings)
    source = ("capability_class", "effort") if serious else ("requested_capability_class", "requested_effort")
    capability = subject.get(source[0]) or subject["capability_class"]
    effort = subject.get(source[1]) or subject["effort"]
    if capability == "deterministic":
        capability = "balanced"
    if effort == "none":
        effort = "medium"
    return capability, effort


def _dependency_met(node: dict[str, Any] | None) -> bool:
    if node is None or node["state"] != "PASSED":
        return False
    return node["integrated"] or node["role"] not in INTEGRATED_ROLES


def _active(record: dict[str, Any]) -> bool:
    return any(node["state"] in ACTIVE_NODE_STATES for node in record["nodes"].values())


def _count_passed(record: dict[str, Any]) -> int:
    return sum(1 for node in record["nodes"].values() if node["state"] == "PASSED")


def _insert_after(order: list[str], anchor: str, node_id: str) -> None:
    if node_id in order:
        return
    try:
        index = max(i for i, item in enumerate(order) if item == anchor or item.startswith(anchor + "."))
    except ValueError:
        order.append(node_id)
        return
    order.insert(index + 1, node_id)


def _push_failure(node: dict[str, Any], kind: str, provider: str | None, detail: str) -> None:
    node["failures"].append({"kind": kind, "provider": provider, "detail": redact(detail, 300), "at": now()})
    del node["failures"][:-MAX_FAILURES_KEPT]


def _evidence_line(validation: dict[str, Any]) -> str:
    parts = []
    for item in validation.get("evidence", []):
        status = "ok" if item["passed"] else "FAIL"
        parts.append(f"{item.get('name')}={status}" + (f" ({item['detail']})" if not item["passed"] and item.get("detail") else ""))
    return redact("; ".join(parts) or "no validators", 400)


def _prior_attempts(node: dict[str, Any]) -> str:
    lines = []
    for failure in node["failures"][-3:]:
        lines.append(f"- previous attempt: {failure['kind']}: {failure['detail']}")
    for decision in node.get("decisions", [])[-3:]:
        lines.append(f"- operator decision: {decision}")
    if not lines:
        return ""
    return "\n\nContext from earlier attempts on this assignment (your worktree keeps their partial work):\n" + "\n".join(lines) + "\n"


def _node_view(node: dict[str, Any]) -> dict[str, Any]:
    selection = node.get("selection") or {}
    worktree = node.get("worktree") or {}
    return {
        "id": node["id"],
        "role": node["role"],
        "goal": node["goal"][:240],
        "state": node["state"],
        "wait_reason": node.get("wait_reason"),
        "subject": node.get("subject"),
        "depends_on": node["depends_on"],
        "scope": node["scope"],
        "capability_class": node["capability_class"],
        "requested_capability_class": node["requested_capability_class"],
        "effort": node["effort"],
        "execution_path": node["execution_path"],
        "provider": selection.get("provider"),
        "model": selection.get("model"),
        "provider_effort": selection.get("provider_effort"),
        "selection_reason": selection.get("reason"),
        "overridden": selection.get("overridden", False),
        "branch": worktree.get("branch"),
        "worktree": worktree.get("path"),
        "attempts": node["attempts"],
        "retries": node["retries"],
        "escalations": node["escalations"],
        "excluded_providers": node["excluded_providers"],
        "failures": node["failures"][-3:],
        "validation": node.get("validation"),
        "review": node["review"],
        "integrated": node["integrated"],
        "checkpoint": node.get("checkpoint"),
        "result": node.get("result"),
    }
