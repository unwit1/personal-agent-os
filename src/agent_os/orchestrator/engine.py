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
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from ..capabilities import next_class
from ..telemetry import LocalTelemetryStore, TelemetryEvent, TelemetryPrivacyError
from ..timestamps import utc_now_iso as now
from . import planner, prompts
from . import usage as usage_lib
from .adapters import AgentLaunchRequest, AgentResult, RunningAgent, get_adapter
from .adapters.base import kill_tree
from .ledger import Ledger
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
from .stall import repeated_command
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
        session_foreman: bool | None = None,
        foreman_home: Path | None = None,
    ) -> None:
        self.store = store or RunStore()
        # The machine engine (no injected registry) attaches new runs to a live
        # session foreman (foreman_deploy.py); embedded/test engines do not.
        self._session_foreman = (registry is None and registry_path is None) if session_foreman is None else session_foreman
        self._foreman_home = foreman_home
        self._registry = registry
        self._registry_path = registry_path
        self._telemetry = telemetry_store
        self._claims_path = claims_path
        self._sleep = sleep
        self._handles: dict[tuple[str, str], RunningAgent] = {}
        self._adapters: dict[str, Any] = {}
        self._availability: dict[str, bool] | None = None
        self._lock = threading.RLock()
        self.ledger = Ledger(self.store.run_dir)

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
        cooling = _cooling_providers(self.store.home)
        return {key: value and key not in cooling for key, value in self._availability.items()}

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
            ("planner", "reasoning", "medium"),
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
        origin: dict[str, Any] | None = None,
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
            "origin": dict(origin or {"kind": "task"}),
            "worktree_layout": "short",
            "launches": 0,
            "launch_budget": run_policy["max_launches"],
            "integration": {"branch": None, "path": None, "head": None, "merged": []},
            "final": {"validation": None, "repairs": 0, "landed": None, "summary": None},
            "usage": usage_lib.empty_totals(),
            "validation_cache": {},
            "created_at": now(),
            "updated_at": now(),
        }
        if self._session_foreman and planning == "auto":
            from .foreman_deploy import ForemanManager, manager

            attached = (manager() if self._foreman_home is None else ForemanManager(base=self._foreman_home)).attach(identifier)
            if attached:
                record["foreman"] = attached
        self.store.save(record)
        self.store.append_event(identifier, "run.created", detail=f"{planning} plan with {len(nodes)} node(s)"
                                + (f"; planner: session foreman {record['foreman']['model'] or '(deploying)'}" if record.get("foreman") else ""))
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
            # A separate repository nested inside a project folder (a fixture,
            # a vendored checkout) is not that project.
            if identified and identified.get("path") and Path(identified["path"]).resolve() != Path(repo).resolve():
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
            first_start = not record["control"]["started"]
            _operator_changed(record)
            record["control"]["started"] = True
            record["control"]["paused"] = False
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "run.started", detail=f"auto_continue={record['policy']['auto_continue']}")
            if first_start:
                self.ledger.emit(run_id, "run_started", mode="orchestrated run", project=record.get("project"), planning=record["preflight"].get("planning"), auto_continue=record["policy"]["auto_continue"], nodes=len(record["nodes"]))
            return self.summary(record)

    def add_message(self, run_id: str, text: str) -> dict[str, Any]:
        """A message from the operator to the run's agents. Every prompt
        built from now on carries the recent messages (prompts.py)."""
        text = str(text or "").strip()
        if not text:
            raise OrchestratorError("the message is empty")
        with self._lock:
            record = self.store.load(run_id)
            record.setdefault("operator_messages", []).append({"at": now(), "text": text[:2000]})
            _operator_changed(record)
            self.store.save(record)
            self.store.append_event(run_id, "operator.message", None, text[:300])
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
            _operator_changed(record)
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "run.paused", detail="no new work will be dispatched")
            self.ledger.emit(run_id, "run_paused", reason="paused by user")
            return self.summary(record)

    def resume(self, run_id: str, auto_continue: bool | None = None) -> dict[str, Any]:
        with self._lock:
            record = self.store.load(run_id)
            record["control"]["paused"] = False
            record["control"]["stop_requested"] = False
            record["control"]["started"] = True
            _operator_changed(record)
            if auto_continue is not None:
                record["policy"]["auto_continue"] = bool(auto_continue)
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "run.resumed")
            self.ledger.emit(run_id, "run_resumed")
            return self.summary(record)

    def stop(self, run_id: str) -> dict[str, Any]:
        """Cancel running workers now and pause. Partial work stays checkpointed."""
        with self._lock:
            record = self.store.load(run_id)
            record["control"]["paused"] = True
            cancelled = self._cancel_active(record, reason="stopped by user")
            record["control"]["stop_requested"] = bool(cancelled["remote"])
            _operator_changed(record)
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, "run.stopped", detail=f"cancelled {cancelled['count']} worker(s)")
            self.ledger.emit(run_id, "run_paused", reason="stopped by user", workers_cancelled=cancelled["count"])
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
            if approve and gate["kind"] == "consequential_repository_write":
                # Write-ahead: persist the approval and the intent before the
                # base branch moves, so a crash after landing cannot leave the
                # record claiming the gate is still open (IMP-0013).
                record["final"]["landing"] = {"state": "intended", "gate": gate["id"], "at": now()}
                self.store.save(record)
            self._apply_decision(record, gate, approve, gate["note"])
            self._derive_state(record)
            self.store.save(record)
            self.store.append_event(run_id, f"gate.{gate['status']}", gate.get("node"), f"{gate['kind']}: {gate['reason']}")
            from .simple import GATE_CARDS

            title = GATE_CARDS.get(gate["kind"], {}).get("title", gate["kind"].replace("_", " "))
            self.ledger.emit(run_id, "note", gate.get("node"), text=f"You {'approved' if approve else 'declined'}: {title.lower()}", gate=gate_id, approved=approve, kind=gate["kind"])
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
                deferred = node["state"] == "PASSED" and (node.get("integration") or {}).get("deferred")
                if node["state"] == "PASSED" and not deferred:
                    raise OrchestratorError(f"{node_id} already passed; use review-again to re-check it")
                if deferred:
                    # A deferred host action merged nothing; once the host
                    # problem is fixed the step can run again.
                    node["integrated"] = False
                    node["integration"] = None
                    node["completed_at"] = None
                    record["deferred_host_actions"] = [item for item in record.get("deferred_host_actions") or [] if item.get("node") != node_id]
                node["state"] = "FAILED_RETRYABLE"
                node["retries"] = 0
                node["selection"] = None
                node["excluded_providers"] = []  # a retry starts routing afresh
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
            node.setdefault("excluded_classes", {}).pop(provider, None)
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
            _operator_changed(record)
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
            if self._recover_landing(record):
                self.store.save(record)
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
                self.store.refresh_control(record)  # a pause sent during _poll applies before anything launches
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
            transient_errors = 0
            while True:
                # Without Auto Continue, reaching a stage boundary stops new
                # dispatch; workers already running are still collected.
                try:
                    summary = self.step(run_id, dispatch=not boundary)
                except (GitError, OSError):
                    # A git or process call can fail once (a killed child, a
                    # transient lock). Back off and retry rather than leaving
                    # the run without a driver; give up if it keeps failing.
                    transient_errors += 1
                    if transient_errors > TRANSIENT_TICK_RETRIES:
                        raise
                    self._sleep(min(5.0 * 2 ** (transient_errors - 1), 120.0))
                    continue
                transient_errors = 0
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
                if active or (record["state"] == "PLANNING" and str(record.get("state_reason") or "").startswith("waiting for the session foreman")):
                    self._sleep(float(record["policy"]["poll_interval_seconds"]))
                elif str(record.get("state_reason") or "").startswith(USAGE_RESET_WAIT):
                    self._sleep(max(float(record["policy"]["poll_interval_seconds"]), 30.0))
                else:
                    # Nothing running and not stopped (e.g. a node parked on a
                    # deferred repair): without a pause this loop spins a core.
                    self._sleep(max(float(record["policy"]["poll_interval_seconds"]), IDLE_TICK_SECONDS))
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
            if node["state"] == "VALIDATING" and node.get("pending_validation") is not None:
                self._collect_validation(record, node)
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
                elif elapsed > 120 and self._loop_check_due(key):
                    loop = repeated_command(handle.stdout_path)
                    if loop:
                        adapter.cancel(handle)
                        self._handles.pop(key, None)
                        self.store.append_event(record["run_id"], "worker.stuck", node_id, f"{loop['count']} of its last {loop['window']} commands were: {loop['command'][-160:]}")
                        self._fail(record, node, "stuck", f"worker was looping ({loop['count']}/{loop['window']} identical commands); stopped early")
                continue
            result = adapter.collect(handle)
            self._handles.pop(key, None)
            self._finish_worker(record, node, result)

    def _usage_reset_wait(self, record: dict[str, Any], node: dict[str, Any]) -> str | None:
        """When the only reason nothing can run is a provider cooling down
        (usage limit, open breaker), the wait reason naming the earliest
        reset; the node waits for it instead of failing."""
        cooling = _cooling_providers(self.store.home) - set(node.get("excluded_providers") or []) - set(self._paid_blocked(record))
        enabled = {provider["id"] for provider in self.registry().providers if provider.get("enabled", True)}
        cooling &= enabled
        if not cooling:
            return None
        entries = _read_cooldowns(self.store.home)
        until = sorted((str((entries.get(provider) or {}).get("until") or ""), provider) for provider in cooling)
        moment, provider = until[0]
        return f"{USAGE_RESET_WAIT} {provider} at {moment[:16].replace('T', ' ')} UTC"

    def _cheaper_reset_soon(self, record: dict[str, Any], node: dict[str, Any], selection: dict[str, Any]) -> str | None:
        """Wait for a cheaper provider whose usage resets within
        ``wait_for_reset_seconds`` instead of failing over to a costlier one
        (Hermes' min_switch_reset_seconds). 0 turns it off."""
        limit = int(record["policy"].get("wait_for_reset_seconds") or 0)
        capability = selection.get("capability_class")
        chosen = self.registry().get(selection["provider"]) or {}
        chosen_cost = (chosen.get("costs") or {}).get(capability)
        if limit <= 0 or chosen_cost is None:
            return None
        blocked = set(node.get("excluded_providers") or []) | set(self._paid_blocked(record))
        moment = datetime.now(timezone.utc)
        best = None
        for provider_id, entry in _read_cooldowns(self.store.home).items():
            provider = self.registry().get(provider_id)
            if not provider or not provider.get("enabled", True) or provider_id in blocked or not (provider.get("models") or {}).get(capability):
                continue
            cost = (provider.get("costs") or {}).get(capability)
            try:
                until = datetime.fromisoformat(str((entry or {}).get("until")))
            except ValueError:
                continue
            remaining = (until - moment).total_seconds()
            if cost is not None and cost < chosen_cost and 0 < remaining <= limit and (best is None or until < best[0]):
                best = (until, provider_id)
        if best is None:
            return None
        return f"{USAGE_RESET_WAIT} {best[1]} at {best[0].isoformat()[:16].replace('T', ' ')} UTC (cheaper than {selection['provider']}; resets soon)"

    def _loop_check_due(self, key: tuple[str, str], interval: float = 60.0) -> bool:
        """Read a worker's event stream for loops at most once a minute."""
        checks = self.__dict__.setdefault("_loop_checks", {})
        now_ = time.monotonic()
        if now_ - checks.get(key, 0.0) < interval:
            return False
        checks[key] = now_
        return True

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
        model_call = node["execution_path"] == "model"
        call_usage = usage_lib.coerce(result.usage, (node.get("selection") or {}).get("provider") or "unknown") if model_call else usage_lib.unavailable("local")
        node["result"] = {
            "outcome": payload["outcome"],
            "failure_kind": payload["failure_kind"],
            "summary": payload["summary"],
            "self_reported_status": str((structured or {}).get("status") or "")[:40] or None,
            "usage": call_usage,
            "duration_ms": payload["duration_ms"],
            "at": now(),
        }
        usage = record["usage"]
        usage["workers"] += 1
        if model_call:
            usage_lib.add(usage, call_usage)
        self.store.append_event(record["run_id"], "worker.finished", node["id"], f"{result.outcome} {result.failure_kind or ''} {result.summary[:160]}")
        selection = node.get("selection") or {}
        if model_call:
            self.ledger.emit(
                record["run_id"],
                "model_completed" if result.outcome == "completed" else "model_failed",
                node["id"],
                role=node["role"],
                provider=selection.get("provider"),
                model=selection.get("model"),
                capability_class=selection.get("capability_class"),
                effort=selection.get("provider_effort"),
                attempt=node["attempts"],
                failure_kind=result.failure_kind,
                duration_ms=result.duration_ms,
                usage=call_usage,
                prompt_chars=node.get("prompt_chars"),
                prompt_tokens_estimate=usage_lib.estimate_tokens(node["prompt_chars"]) if node.get("prompt_chars") is not None else None,
            )
        else:
            self.ledger.emit(record["run_id"], "local_execution", node["id"], what=f"deterministic step {node['id']}", passed=result.outcome == "completed")
            self.ledger.emit(
                record["run_id"],
                "work_avoided",
                node["id"],
                category="deterministic",
                model_calls_avoided=1,
                reason="a planned deterministic command did this step instead of a model worker",
                tokens_avoided_estimate=self._measured_average(record, "implementer"),
                estimate_basis="average exact input+output tokens of implementer calls in this run" if self._measured_average(record, "implementer") else None,
            )
        if result.outcome != "completed":
            self._record_telemetry(record, node, result, validator_passed=None)
            self._fail(
                record,
                node,
                result.failure_kind or "process_error",
                result.detail or "worker failed",
                allow_fallback=not model_call and node.get("execution_path") == "deterministic",
            )
            return
        status = structured.get("status") if isinstance(structured, dict) else None
        if status in {"needs_decision", "blocked_on_host"}:
            if node["worktree"] and node["role"] in {"implementer", "test_author", "repairer"}:
                self._checkpoint(record, node, "needs decision")
            question = redact(structured.get("question") or structured.get("summary") or "the agent needs a decision", 500)
            # A host-level prerequisite is not a decision a person can answer
            # through the gate: approving only relaunched the same worker, which
            # asked again. Defer it and keep the run moving instead.
            if status == "blocked_on_host" or _host_action(question) or len(node.get("decisions") or []) >= 2:
                self._defer_host_action(record, node, question)
                self._record_telemetry(record, node, result, validator_passed=None)
                return
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
        foreman = record.get("foreman") or {}
        if foreman.get("applied") and foreman.get("status") != "fallback":
            from .foreman_strategy import apply as apply_strategy

            structured, guarded = apply_strategy(record["goal"], structured, foreman.get("strategy"))
            for note in guarded:
                self.store.append_event(record["run_id"], "plan.adjusted", node["id"], note)
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
        affected = self._affected_tests_first(record, node, validators, worktree["path"], changed)
        if affected is not None and not affected["passed"]:
            # Fail fast: a new failure in the affected modules already decides
            # this attempt; the full suite would only repeat it more slowly.
            scoped = run_all([], worktree["path"], changed=changed, scope=node["scope"], control_plane=_control_plane(record, node))
            validation = {"passed": False, "declared_validators": len(validators), "evidence": [*scoped["evidence"], affected], "fail_fast": True, "at": now()}
            self._after_validation(record, node, structured, changed, validation)
            return
        validation = self._validate_cached(record, node, validators, worktree["path"], changed=changed, scope=node["scope"])
        if validation is None:
            # The suite runs in the background; the driver keeps collecting
            # and dispatching meanwhile and finishes this node when it is done.
            node["pending_validation"] = {"structured": structured, "affected": affected, "changed": changed, "validators": validators}
            self._submit_validation(record, node, validators, worktree["path"], changed, node["scope"])
            return
        if affected is not None:
            validation["evidence"] = [affected, *validation["evidence"]]
        self._after_validation(record, node, structured, changed, validation)

    def _submit_validation(self, record: dict[str, Any], node: dict[str, Any], validators: list[dict[str, Any]], cwd: str | Path, changed: list[str] | None, scope: list[str] | None) -> None:
        from concurrent.futures import ThreadPoolExecutor

        size = max(int(record["policy"].get("max_parallel_validations") or 1), 1)
        pool = self.__dict__.get("_validation_pool")
        if pool is None or self.__dict__.get("_validation_pool_size") != size:
            pool = ThreadPoolExecutor(max_workers=size, thread_name_prefix="agent-os-validate")
            self.__dict__["_validation_pool"], self.__dict__["_validation_pool_size"] = pool, size
        control = _control_plane(record, node)
        timeout = int(record["policy"]["worker_timeout_seconds"])
        self.ledger.emit(record["run_id"], "tests_started", node["id"], validators=len(validators))
        started = time.monotonic()

        def work() -> tuple[dict[str, Any], float]:
            # Subprocesses only: the run record is never touched off the driver thread.
            result = run_all(validators, cwd, changed=changed, scope=scope, timeout=timeout, control_plane=control)
            return result, round(time.monotonic() - started, 2)

        self.__dict__.setdefault("_validations", {})[(record["run_id"], node["id"])] = pool.submit(work)

    def _collect_validation(self, record: dict[str, Any], node: dict[str, Any]) -> None:
        """Finish a node whose background validation is done; re-submit one
        a previous driver process started but never collected."""
        key = (record["run_id"], node["id"])
        pending = node.get("pending_validation") or {}
        validators = pending.get("validators") or node["validators"] or record["policy"]["default_validators"]
        futures = self.__dict__.setdefault("_validations", {})
        future = futures.get(key)
        if future is None:
            self._submit_validation(record, node, validators, node["worktree"]["path"], pending.get("changed"), node["scope"])
            return
        if not future.done():
            return
        futures.pop(key, None)
        node.pop("pending_validation", None)
        try:
            validation, duration = future.result()
        except Exception as exc:  # the validator runner itself broke
            validation = {"passed": False, "declared_validators": 0, "evidence": [{"name": "validation", "kind": "command", "passed": False, "detail": redact(f"validation crashed: {exc}", 300)}]}
            duration = 0.0
        validation = self._validate_record(record, node, validators, node["worktree"]["path"], validation, duration)
        if pending.get("affected") is not None:
            validation["evidence"] = [pending["affected"], *validation["evidence"]]
        self._after_validation(record, node, pending.get("structured"), pending.get("changed") or [], validation)

    def _after_validation(self, record: dict[str, Any], node: dict[str, Any], structured: dict[str, Any] | None, changed: list[str], validation: dict[str, Any]) -> None:
        validation["changed_files"] = changed[:50]
        guard = _publication_guard(record, node)
        if guard is not None:
            validation["evidence"].append(guard)
            if not guard["passed"]:
                validation["passed"] = False
        node["validation"] = validation
        self.store.append_event(record["run_id"], "validation." + ("passed" if validation["passed"] else "failed"), node["id"], _evidence_line(validation))
        if not validation["passed"]:
            self._validation_failed(record, node, validation)
            return
        if not changed and node["role"] in INTEGRATED_ROLES and node["review"]["rounds"] == 0:
            if str((structured or {}).get("status")) != "already_done":
                # "Done" with no change is a failed attempt, not a success:
                # passing tests only prove nothing broke.
                self.ledger.emit(record["run_id"], "loop_guard", node["id"], guard="no_change_reported_done", reason="the worker reported done but changed no files")
                self._validation_failed(record, node, {"evidence": [{"name": "produced-changes", "kind": "check", "passed": False, "detail": "reported done but changed no files; if the work already exists, report status already_done"}]}, reason="it reported done but changed no files")
                return
            # The worker says the work already exists: nothing to review or
            # integrate, and a reviewer call would read an empty diff.
            node["state"] = "PASSED"
            node["completed_at"] = now()
            node["review_required"] = False
            self.ledger.emit(
                record["run_id"],
                "work_avoided",
                node["id"],
                category="no_change",
                model_calls_avoided=1 if self._review_required(record, {**node, "review_required": None}) else 0,
                reason="the work already existed (worker reported already_done), so no review was requested",
                tokens_avoided_estimate=self._measured_average(record, "reviewer"),
                estimate_basis="average exact input+output tokens of reviewer calls in this run" if self._measured_average(record, "reviewer") else None,
            )
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

    def _affected_tests_first(self, record: dict[str, Any], node: dict[str, Any], validators: list[dict[str, Any]], cwd: str | Path, changed: list[str]) -> dict[str, Any] | None:
        """IMP-0006: run the import-graph-selected test modules before the
        full validators. Returns the evidence item, or None when the step does
        not apply. Failures that already fail on the base commit (per the
        project validator's baseline) are excused, like the full suite's."""
        import sys

        from .test_selection import affected_first_validator, runs_unit_tests
        from .validators import run_validator

        project = [item for item in validators if str(item.get("name", "")).startswith("project-validation")]
        mode = record["policy"].get("affected_tests_first", "retries")
        mode = {True: "always", False: "off"}.get(mode, mode) if isinstance(mode, bool) else mode
        retrying = int(node.get("attempts") or 1) > 1 or node["role"] == "repairer"
        if mode == "off" or (mode == "retries" and not retrying) or not changed or not project or not runs_unit_tests(project):
            return None
        step = affected_first_validator(changed, cwd, sys.executable)
        if step is None:
            return None
        started = time.monotonic()
        result = run_validator({key: step[key] for key in ("kind", "name", "command")}, cwd, int(record["policy"]["worker_timeout_seconds"]))
        result.update(kind="affected", selected=len(step["selected"]), of=step["of"], seconds=round(time.monotonic() - started, 2))
        if not result["passed"] and result.get("failed_tests"):
            known = self._baseline_failures(record, project[0])
            if known is not None and set(result["failed_tests"]) <= set(known):
                result.update(passed=True, baseline_failures=len(result["failed_tests"]), detail=redact(f"only failures already present on the base commit ({len(result['failed_tests'])})", 400))
            elif known is not None:
                new = sorted(set(result["failed_tests"]) - set(known))
                result.update(new_failures=new[:20], detail=redact(f"broken by this change (affected tests): {', '.join(new[:5])}", 400))
        self.ledger.emit(record["run_id"], "tests_completed", node["id"], selection="affected", selected=result["selected"], of=result["of"], passed=result["passed"], duration_s=result["seconds"], **_test_totals([result]))
        return result

    def _validate(
        self,
        record: dict[str, Any],
        node: dict[str, Any] | None,
        validators: list[dict[str, Any]],
        cwd: str | Path,
        *,
        changed: list[str] | None = None,
        scope: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run validators now, reusing an identical tree's earlier result."""
        cached = self._validate_cached(record, node, validators, cwd, changed=changed, scope=scope)
        if cached is not None:
            return cached
        self.ledger.emit(record["run_id"], "tests_started", node["id"] if node else None, validators=len(validators))
        started = time.monotonic()
        validation = run_all(validators, cwd, changed=changed, scope=scope, timeout=int(record["policy"]["worker_timeout_seconds"]), control_plane=_control_plane(record, node))
        return self._validate_record(record, node, validators, cwd, validation, round(time.monotonic() - started, 2))

    def _validate_cached(
        self,
        record: dict[str, Any],
        node: dict[str, Any] | None,
        validators: list[dict[str, Any]],
        cwd: str | Path,
        *,
        changed: list[str] | None = None,
        scope: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """An earlier result for identical code, or None when the validators must run.

        Validator results are cached per run by (Git tree, validator list).
        The same tree with the same commands cannot give a different answer
        unless the tests are flaky, so re-running them only costs time; set
        policy ``reuse_validation`` to false for flaky suites. The editable
        scope check is always recomputed.
        """
        run_id = record["run_id"]
        node_id = node["id"] if node else None
        tree = _tree_hash(cwd)
        key = _validation_key(tree, validators) if tree and record["policy"].get("reuse_validation", True) else None
        cache = record.setdefault("validation_cache", {})
        cached = cache.get(key) if key else None
        if cached is not None and any(
            not item["passed"] and str(item.get("name", "")).startswith("project-validation") and "failed_tests" not in item
            for item in cached["evidence"]
        ):
            # Recorded before failing tests were itemized, so it cannot be
            # compared with the base commit; run it again.
            cached = None
        if cached is not None:
            scoped = run_all([], cwd, changed=changed, scope=scope, control_plane=_control_plane(record, node)) if changed is not None else {"evidence": []}
            evidence = [*scoped["evidence"], *(dict(item) for item in cached["evidence"])]
            validation = {
                "passed": all(item["passed"] for item in evidence),
                "declared_validators": cached["declared_validators"],
                "evidence": evidence,
                "reused": {"tree": tree[:12], "from": cached["at"]},
                "at": now(),
            }
            self._excuse_baseline_failures(record, node_id, validators, validation)
            self.ledger.emit(run_id, "cache_hit", node_id, what="test results for identical code", tree=tree[:12])
            self.ledger.emit(run_id, "tests_completed", node_id, reused=True, passed=validation["passed"], **_test_totals(cached["evidence"]))
            self.ledger.emit(run_id, "work_avoided", node_id, category="validation_cache", model_calls_avoided=0, reason="identical code was already tested in this run", seconds_avoided=cached.get("duration_s"), tokens_avoided_estimate=None)
            if not cached["passed"]:
                self.ledger.emit(run_id, "loop_guard", node_id, guard="unchanged_code_retest", reason="no new code since the last failed test run; tests were not run again")
            return validation
        return None

    def _validate_record(self, record: dict[str, Any], node: dict[str, Any] | None, validators: list[dict[str, Any]], cwd: str | Path, validation: dict[str, Any], duration: float) -> dict[str, Any]:
        """Baseline excuse, cache entry and telemetry for a fresh validation (driver thread only)."""
        run_id = record["run_id"]
        node_id = node["id"] if node else None
        tree = _tree_hash(cwd)
        key = _validation_key(tree, validators) if tree and record["policy"].get("reuse_validation", True) else None
        cache = record.setdefault("validation_cache", {})
        self._excuse_baseline_failures(record, node_id, validators, validation)
        validation["at"] = now()
        commands = [item for item in validation["evidence"] if item["kind"] != "scope"]
        if key:
            cache[key] = {"evidence": commands, "declared_validators": validation["declared_validators"], "passed": all(item["passed"] for item in commands), "at": validation["at"], "duration_s": duration}
            for stale in list(cache)[:-50]:
                del cache[stale]
        self.ledger.emit(run_id, "tests_completed", node_id, passed=validation["passed"], duration_s=duration, **_test_totals(commands))
        return validation

    def _excuse_baseline_failures(self, record: dict[str, Any], node_id: str | None, validators: list[dict[str, Any]], validation: dict[str, Any]) -> None:
        """Judge a project-wide suite by what the change broke, not by what was
        already broken.

        A suite that already fails on the base commit (tests that depend on the
        user's machine, for example) otherwise fails every worker, escalates it
        to costlier models, and ends in failure without anyone having broken
        anything. Only project validators are compared; a task's own validators
        must pass outright."""
        by_name = {item.get("name"): item for item in validators}
        for item in validation["evidence"]:
            validator = by_name.get(item.get("name"))
            if item["passed"] or not validator or not str(item.get("name", "")).startswith("project-validation") or not item.get("failed_tests"):
                continue
            known = self._baseline_failures(record, validator)
            if known is None:
                continue
            new = sorted(set(item["failed_tests"]) - set(known))
            if new:
                # The retry prompt carries this line: name what broke, not
                # just a failure count, so the next attempt can fix it.
                item["new_failures"] = new[:20]
                excused = len(item["failed_tests"]) - len(new)
                item["detail"] = redact(f"broken by this change: {', '.join(new[:5])}" + (f"; {excused} other failure(s) also fail on the base commit" if excused else ""), 400)
                continue
            item["passed"] = True
            item["baseline_failures"] = len(item["failed_tests"])
            item["detail"] = redact(f"only failures already present on the base commit ({len(item['failed_tests'])}); none introduced", 400)
            self.store.append_event(record["run_id"], "validation.baseline_excused", node_id, f"{item['name']}: {len(item['failed_tests'])} pre-existing failure(s)")
        validation["passed"] = all(item["passed"] for item in validation["evidence"])

    def _baseline_failures(self, record: dict[str, Any], validator: dict[str, Any]) -> list[str] | None:
        """Failing tests for ``validator`` on the run's base commit, measured once per run."""
        import json

        from .validators import run_validator
        from .worktrees import git

        baselines = record.setdefault("validation_baseline", {})
        key = json.dumps(validator.get("command"), sort_keys=True, default=str)
        if key in baselines:
            return baselines[key]
        repo = Path(record["repository"])
        path = self.store.run_dir(record["run_id"]) / "baseline"
        known = None
        try:
            git(["worktree", "remove", "--force", str(path)], repo, check=False)
            git(["worktree", "prune"], repo, check=False)
            git(["worktree", "add", "--detach", str(path), record["base_commit"]], repo)
            outcome = run_validator(validator, path, int(record["policy"]["worker_timeout_seconds"]))
            known = [] if outcome["passed"] else (outcome.get("failed_tests") or None)
        except GitError as exc:
            self.store.append_event(record["run_id"], "validation.baseline_unavailable", None, redact(exc, 300))
        finally:
            try:
                git(["worktree", "remove", "--force", str(path)], repo)
            except GitError:
                pass
        baselines[key] = known
        self.store.append_event(record["run_id"], "validation.baseline", None, f"{validator.get('name')}: {'unknown' if known is None else len(known)} failure(s) on the base commit")
        return known

    def _measured_average(self, record: dict[str, Any], role: str) -> int | None:
        """Average exact provider tokens (input + output) of this run's
        completed calls for ``role``; the only basis used for "tokens avoided"
        estimates. ``None`` when nothing was measured."""
        totals = []
        for node in record["nodes"].values():
            usage = (node.get("result") or {}).get("usage") or {}
            if node["role"] == role and usage.get("accuracy") == "exact" and usage.get("source") != "synthetic" and usage.get("input_tokens") is not None:
                totals.append(int(usage["input_tokens"]) + int(usage.get("output_tokens") or 0))
        return int(sum(totals) / len(totals)) if totals else None

    def _validation_failed(self, record: dict[str, Any], node: dict[str, Any], validation: dict[str, Any], reason: str = "its tests failed") -> None:
        detail = _evidence_line(validation)
        _push_failure(
            node,
            "validator_failed",
            (node.get("selection") or {}).get("provider"),
            detail,
            node.get("capability_class"),
        )
        policy = record["policy"]
        if self._fallback_to_model(record, node, "validator_failed", detail):
            return
        if node["execution_path"] == "model" and node["escalations"] < policy["max_escalations"]:
            before = f"{node['capability_class']}/{node['effort']}"
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
                self.ledger.emit(record["run_id"], "model_escalated", node["id"], **{"from": before, "to": label, "reason": reason, "evidence": detail, "escalation": node["escalations"]})
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
        self.ledger.emit(record["run_id"], "loop_guard", node["id"], guard="escalation_limit", reason=f"stopped after {node['escalations']} escalation(s); tests still fail")

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
        for item in subject["review"]["findings"]:
            if item["round"] != round_number and item["disposition"] == "open":
                # This round's reviewer was shown them and re-reported the
                # ones that still apply; the older entries are superseded.
                item["disposition"] = "superseded"
        blocking = material(this_round, record["policy"]["material_severities"])
        self.store.append_event(record["run_id"], "review.completed", subject["id"], f"{parsed['verdict']}; {len(blocking)} material finding(s)")
        self.ledger.emit(
            record["run_id"], "review_completed", reviewer["id"], subject=subject["id"], provider=provider,
            verdict=parsed["verdict"], findings=len(parsed["findings"]), material_findings=len(blocking),
            independent_provider=bool(author and provider != author), round=round_number,
        )
        if not blocking and parsed["verdict"] != "blocked":
            subject["state"] = "PASSED"
            subject["completed_at"] = now()
            return
        if subject["review"]["rounds"] < record["policy"]["max_review_rounds"]:
            subject["state"] = "NEEDS_REPAIR"
            self._create_repair(record, subject, blocking)
            return
        if not subject["review"].get("escalated"):
            # Before asking a person, let one stronger reviewer judge the
            # disagreement; a cheap reviewer's false positive otherwise stops
            # the run on a human.
            subject["review"]["escalated"] = True
            subject["state"] = "WAITING_FOR_REVIEW"
            self.ledger.emit(record["run_id"], "loop_guard", subject["id"], guard="review_escalated", reason="findings remain after the allowed rounds; asking a stronger reviewer before a person")
            self._create_reviewer(record, subject, capability="reasoning")
            return
        if not subject["review"].get("final_repair"):
            # The stronger reviewer confirmed the findings, so they are real
            # and concrete: one last repair before asking a person (once).
            subject["review"]["final_repair"] = True
            subject["review"]["final_repair_ids"] = [item["id"] for item in blocking]
            subject["state"] = "NEEDS_REPAIR"
            self.ledger.emit(record["run_id"], "loop_guard", subject["id"], guard="final_repair", reason="a stronger reviewer confirmed the findings; one last repair before asking you")
            self._create_repair(record, subject, blocking)
            return
        repaired = subject["review"].get("final_repair_ids") or []
        new = [item for item in blocking if not any(item["id"] == fid or item["id"].endswith("-" + fid) for fid in repaired)]
        if new and len(new) == len(blocking) and not subject["review"].get("extra_repair"):
            # Every blocking finding is new in the review after the final
            # repair: no worker has been asked to fix them yet. One more
            # bounded repair (once per node) instead of waiting on a person.
            subject["review"]["extra_repair"] = True
            subject["state"] = "NEEDS_REPAIR"
            self.ledger.emit(record["run_id"], "loop_guard", subject["id"], guard="extra_repair", reason="the last review raised only new findings; one bounded repair before asking you")
            self._create_repair(record, subject, blocking)
            return
        self.ledger.emit(record["run_id"], "loop_guard", subject["id"], guard="review_rounds", reason=f"stopped the review/fix cycle after {subject['review']['rounds']} round(s); asking you instead")
        subject["state"] = "APPROVAL_REQUIRED"
        self._open_gate(
            record,
            "unresolved_review_findings",
            f"{len(blocking)} material finding(s) remain after {subject['review']['rounds']} review round(s)",
            subject["id"],
        )

    def _create_reviewer(self, record: dict[str, Any], subject: dict[str, Any], extra_round: bool = False, capability: str | None = None) -> None:
        subject["review"]["rounds"] += 1
        round_number = subject["review"]["rounds"]
        reviewer_id = f"{subject['id']}.review{round_number}"
        capability = capability or subject["requested_capability_class"]
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

    def _fail(self, record: dict[str, Any], node: dict[str, Any], kind: str, detail: str, *, allow_fallback: bool = False) -> None:
        provider = (node.get("selection") or {}).get("provider")
        _push_failure(node, kind, provider, detail, node.get("capability_class"))
        if provider and kind == "quota":
            # Remember the quota for every node and run on this machine, so
            # later nodes route elsewhere instead of each failing on it first.
            until = _quota_reset(detail)
            _write_cooldown(self.store.home, provider, until, redact(detail, 200))
            self._availability = None
            self.store.append_event(record["run_id"], "provider.cooldown", node["id"], f"{provider} skipped until {until}")
        elif provider and kind == "unavailable":
            opened = _health.record_unavailable(self.store.home, provider, redact(detail, 200))
            if opened:
                self._availability = None
                self.store.append_event(record["run_id"], "provider.cooldown", node["id"], f"{provider} breaker open until {opened} (repeated unavailable)")
        if node["worktree"] and node["role"] in {"implementer", "test_author", "repairer"}:
            try:
                self._checkpoint(record, node, f"partial after {kind}")
            except GitError:
                pass
        self.store.append_event(record["run_id"], f"node.{kind}", node["id"], detail)
        if allow_fallback and kind != "cancelled" and self._fallback_to_model(record, node, kind, detail):
            return
        if kind == "cancelled":
            node["state"] = "FAILED_RETRYABLE"
            node["selection"] = None
            node["wait_reason"] = "cancelled; will resume when the run resumes"
            return
        policy = record["policy"]
        if provider and kind == "invalid_model" and policy["provider_failover"]:
            capability = (node.get("selection") or {}).get("capability_class")
            self._learn_unavailable_model(provider, (node.get("selection") or {}).get("model"), detail)
            if capability:
                excluded = node.setdefault("excluded_classes", {}).setdefault(provider, [])
                if capability not in excluded:
                    excluded.append(capability)
                    self.store.append_event(record["run_id"], "provider.class_failover", node["id"], f"{provider}/{capability} excluded after invalid_model")
                    self.ledger.emit(record["run_id"], "fallback", node["id"], from_provider=provider, reason=kind, capability_class=capability)
        elif provider and policy["provider_failover"]:
            same_kind = [
                item
                for item in node["failures"]
                if item["provider"] == provider
                and item["kind"] in {"process_error", "timeout", "stuck", "interrupted", "malformed"}
                and item.get("capability_class", node["capability_class"]) == node["capability_class"]
            ]
            # A quota is temporary and already recorded machine-wide as a
            # cooldown until its reset; excluding the provider for the node as
            # well would leave it unroutable after the reset.
            if (kind in PROVIDER_FAILURES and kind != "quota") or len(same_kind) >= 2:
                if provider not in node["excluded_providers"]:
                    node["excluded_providers"].append(provider)
                    self.store.append_event(record["run_id"], "provider.failover", node["id"], f"{provider} excluded for this node after {kind}")
                    self.ledger.emit(record["run_id"], "fallback", node["id"], from_provider=provider, reason=kind)
        node["retries"] += 1
        if node["retries"] > policy["max_stage_retries"]:
            selection = node.get("selection") or {}
            if (
                kind == "malformed"
                and node["role"] == "planner"
                and not selection.get("overridden")
                and node["escalations"] < policy["max_escalations"]
            ):
                rung = _next_rung(node)
                if rung:
                    previous_class = node["capability_class"]
                    for failure in node["failures"]:
                        failure.setdefault("capability_class", previous_class)
                    before = f"{node['capability_class']}/{node['effort']}"
                    node["capability_class"] = rung["capability_class"]
                    node["effort"] = rung["effort"]
                    node["escalations"] += 1
                    node["retries"] = 0
                    node["excluded_providers"] = []
                    node["state"] = "FAILED_RETRYABLE"
                    node["selection"] = None
                    label = f"{rung['capability_class']}/{rung['effort']}"
                    node["wait_reason"] = f"planner response malformed; escalated to {label}"
                    self.store.append_event(
                        record["run_id"],
                        "node.escalated",
                        node["id"],
                        f"{before} -> {label} after malformed planner output",
                    )
                    return
            node["state"] = "FAILED_FINAL"
            node["wait_reason"] = f"{kind} after {node['retries'] - 1} retr(ies): {redact(detail, 200)}"
            self.ledger.emit(record["run_id"], "loop_guard", node["id"], guard="retry_limit", reason=f"stopped retrying after {node['retries'] - 1} retr(ies) ({kind})")
            return
        node["state"] = "FAILED_RETRYABLE"
        node["selection"] = None
        node["wait_reason"] = f"{kind}; retry {node['retries']}/{policy['max_stage_retries']} will re-route"
        self.ledger.emit(record["run_id"], "retry", node["id"], reason=kind, retry=node["retries"], limit=policy["max_stage_retries"])

    def _fallback_to_model(self, record: dict[str, Any], node: dict[str, Any], kind: str, detail: str) -> bool:
        """Use only a declared model fallback after concrete deterministic failure."""
        if node.get("execution_path") != "deterministic" or "model" not in node.get("fallback_execution_paths", []):
            return False
        from .model import default_ladder
        from ..capabilities import explain_execution_path

        capability = node.get("capability_class")
        effort = node.get("effort")
        if capability == "deterministic":
            capability, effort = "balanced", "medium"
            node["capability_class"] = node["requested_capability_class"] = capability
            node["effort"] = node["requested_effort"] = effort
        node["execution_path"] = "model"
        node["fallback_execution_paths"] = []
        node["execution_route"] = explain_execution_path(
            node.get("preferred_execution_path", "deterministic"),
            node.get("available_execution_paths", ["deterministic", "model"]),
            "model",
        )
        node["ladder"] = default_ladder(capability, effort, "model")
        node["ladder_step"] = 0
        node["state"] = "FAILED_RETRYABLE"
        node["selection"] = None
        node["wait_reason"] = f"{kind}; declared model fallback selected after deterministic evidence: {redact(detail, 180)}"
        self.store.append_event(record["run_id"], "execution_path.fallback", node["id"], node["wait_reason"])
        self.ledger.emit(record["run_id"], "fallback", node["id"], from_path="deterministic", to_path="model", reason=kind)
        return True

    def _checkpoint(self, record: dict[str, Any], node: dict[str, Any], label: str) -> None:
        worktree = node["worktree"]
        if not worktree:
            return
        commit = self._manager(record).checkpoint(worktree["path"], f"agent-os {record['run_id']}/{node['id']}: {label}")
        node["checkpoint"] = {"commit": commit or head_commit(worktree["path"]), "label": label, "at": now()}
        self.ledger.emit(record["run_id"], "checkpoint_created", node["id"], commit=node["checkpoint"]["commit"][:12], new_commit=bool(commit), label=label)
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
                if selection.get("provider") and node["state"] != "VALIDATING":  # tests are running, not a model
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
            if holds and scopes_overlap(_hard_scope(node), _hard_scope(other)):
                blockers.append(other["id"])
        return blockers

    def _paid_blocked(self, record: dict[str, Any]) -> list[str]:
        """Providers billed to outside credits, when this run may not spend them."""
        if (record.get("policy") or {}).get("allow_paid_spend"):
            return []
        from .model_profile import is_paid

        return [provider["id"] for provider in self.registry().providers if is_paid(provider)]

    def _context_misfit(self, provider_id: str, prompt: str) -> str | None:
        """A reason when prompt + harness overhead + an output reserve exceeds
        85% of the provider's declared context window; None when it fits or
        no window is declared."""
        window = ((self.registry().get(provider_id) or {}).get("profile") or {}).get("context_window")
        if not window:
            return None
        try:
            overhead = int(getattr(self._adapter(provider_id), "context_overhead_tokens", 0) or 0)
        except Exception:
            overhead = 0
        needed = int(len(prompt) / 3.5) + overhead + min(8192, window // 10)
        if needed <= window * 0.85:
            return None
        return f"request ~{needed:,} tokens (prompt + harness + output reserve) does not fit {provider_id}'s {window:,}-token context window"

    def _learn_unavailable_model(self, provider: str, model: str | None, detail: str) -> None:
        """Remember machine-wide that this account cannot use ``model`` on
        ``provider`` so later runs never route to it (file registries only)."""
        path = self.registry().path
        if not model or not path or path == "<inline>":
            return
        from .provider_health import record_unavailable_model

        try:
            record_unavailable_model(Path(path).parent, provider, model, detail)
        except OSError:
            return
        self.reload_providers()

    def _foreman_strategy(self, provider_id: str, model: str) -> dict[str, Any] | None:
        """How this foreman should plan, from measured/benchmark/tier evidence (foreman_strategy)."""
        try:
            from . import foreman_strategy, model_value

            provider = self.registry().get(provider_id) or {}
            model = (provider.get("models") or {}).get(model, model)
            strategy = foreman_strategy.strategy_for(model, provider=provider, evidence=model_value.load_evidence(),
                                                     reports=foreman_strategy._eval_reports(self.store.home / "foreman-eval"))
            return {key: strategy[key] for key in ("model", "score", "band", "source", "summary", "planner_addendum", "guard")}
        except Exception:
            return None

    def _foreman_gate(self, record: dict[str, Any], node: dict[str, Any]) -> bool:
        """Planner of a run attached to the session foreman: wait while it
        deploys, route to it once it serves, fall back to the normal planner
        when it is gone. A planner override the user set wins. True = launch."""
        from .foreman_deploy import planner_hold

        info = record["foreman"]
        roles = record["overrides"].setdefault("roles", {})
        if info.get("status") == "fallback" or (roles.get("planner") and not info.get("applied")):
            return True
        unavailable = {provider for provider, ok in self.availability().items() if not ok}
        paid = set(self._paid_blocked(record))
        hold = planner_hold(record, self._foreman_home, unavailable | paid)
        if "wait" in hold and paid and "wait" not in planner_hold(record, self._foreman_home, unavailable):
            # Only paid foremen are left and this run may not spend outside credits:
            # plan with the normal (subscription) planner instead of waiting.
            hold = {"fallback": "the session foreman uses paid outside credits, which are off for this run"}
        if "wait" in hold:
            node["state"] = "RUNNABLE"
            node["wait_reason"] = hold["wait"]
            return False
        if "provider" in hold:
            if self.registry().get(hold["provider"]) is None:
                self.reload_providers()  # registered by the GUI process after this engine loaded
            if self.registry().get(hold["provider"]) is not None:
                roles["planner"] = {"provider": hold["provider"], **({"model": hold["override_model"]} if hold.get("override_model") else {})}
                if info.get("provider") != hold["provider"]:
                    note = f" (backup for {hold['backup_for']}, which is unavailable)" if hold.get("backup_for") else ""
                    self.store.append_event(record["run_id"], "foreman.backup" if hold.get("backup_for") else "foreman.applied", node["id"],
                                            f"planner -> session foreman {hold['provider']} ({hold['model']}){note}")
                info.update(applied=True, provider=hold["provider"], model=hold["model"], backup_for=hold.get("backup_for"))
                info["strategy"] = self._foreman_strategy(hold["provider"], hold.get("override_model") or hold["model"])
                return True
            hold = {"fallback": f"session foreman provider {hold['provider']} is not registered"}
        if info.get("applied"):
            roles.pop("planner", None)
        info.update(status="fallback", reason=hold["fallback"])
        self.store.append_event(record["run_id"], "foreman.fallback", node["id"], f"{hold['fallback']}; using the normal planner")
        return True

    def _launch(self, record: dict[str, Any], node: dict[str, Any], running: dict[str, int]) -> bool:
        policy = record["policy"]
        if node["role"] == "planner" and record.get("foreman") and not self._foreman_gate(record, node):
            return False
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
            excluded=node["excluded_providers"] + self._paid_blocked(record),
            excluded_classes=node.get("excluded_classes", {}),
            avoid=avoid,
            running=running,
            override=self._override_for(record, node),
            require_avoid=node["role"] == "reviewer" and policy["require_distinct_review_provider"],
            # Reviewers and repairers read the subject's work, so they inherit its
            # workload requirements (e.g. deployment=local for private code).
            requirements=node.get("requirements") or (subject or {}).get("requirements"),
        )
        if not selection.get("resolved"):
            if selection.get("waiting"):
                node["state"] = "RUNNABLE"
                node["wait_reason"] = selection["reason"]
                return False
            reset = self._usage_reset_wait(record, node)
            if reset:
                if node.get("wait_reason") != reset:
                    self.store.append_event(record["run_id"], "node.waiting", node["id"], reset)
                node["state"] = "RUNNABLE"
                node["wait_reason"] = reset
                return False
            node["state"] = "FAILED_FINAL"
            node["wait_reason"] = f"no provider: {selection['reason']}"
            self.store.append_event(record["run_id"], "node.unroutable", node["id"], selection["reason"])
            return False
        wait = None if selection.get("overridden") else self._cheaper_reset_soon(record, node, selection)
        if wait:
            if node.get("wait_reason") != wait:
                self.store.append_event(record["run_id"], "node.waiting", node["id"], wait)
            node["state"] = "RUNNABLE"
            node["wait_reason"] = wait
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
            # Findings earlier rounds left open: the new reviewer checks them
            # instead of judging the change from scratch and missing them.
            findings = material(subject["review"]["findings"], policy["material_severities"]) or None
        if node["role"] == "repairer" and subject:
            wanted = set(node.get("finding_ids") or [])
            findings = [item for item in subject["review"]["findings"] if item["id"] in wanted]
        repo_map = None
        if node["role"] == "planner" and policy.get("planner_repo_map"):
            from .repomap import build as build_map

            try:
                mapped = build_map(cwd, record["goal"])
                repo_map = mapped["text"]
                self.ledger.emit(
                    record["run_id"], "context_selected", node["id"], method="local repository map for the planner (no model call)",
                    candidate_items=mapped["stats"]["tracked_files"], selected_items=mapped["stats"]["listed"],
                    selected_tokens_estimate=usage_lib.estimate_tokens(mapped["stats"]["chars"]),
                )
            except Exception as exc:  # the planner still works without a map
                self.ledger.emit(record["run_id"], "note", node["id"], text=f"repository map unavailable: {type(exc).__name__}")
        prompt, context = prompts.build_measured(record, node, diff=diff, findings=findings, repo_map=repo_map, cwd=str(cwd))
        prompt += _prior_attempts(node, policy["material_severities"])
        if policy.get("share_run_history") and node["role"] in {"planner", "implementer", "test_author", "reviewer"}:
            try:
                prompt += _run_history_note(_snapshot_run_history(self.store.home, cwd))
            except OSError as exc:  # the worker still runs, without the history
                self.ledger.emit(record["run_id"], "note", node["id"], text=f"run history snapshot failed: {type(exc).__name__}")
        # Workers registered for inline (self-contained) prompts have no repository tools.
        addendum = (((record.get("foreman") or {}).get("strategy") or {}).get("planner_addendum") or "") if node["role"] == "planner" else ""
        if addendum and (record.get("foreman") or {}).get("provider") == selection["provider"]:
            prompt += "\n\n" + addendum + "\n"
        if node["role"] == "planner" and "inline" in ((self.registry().get(selection["provider"]) or {}).get("roles") or []):
            prompt += ("\n\nYou have no file or shell tools in this call: plan from the goal and the repository map above, "
                       "and name only files the map lists. Answer with the fenced result block only.\n")
        if node["role"] == "reviewer" and subject and subject.get("failures"):
            # Without this a reviewer flags the fix for a test the author was
            # told it broke as "unrelated to the assignment".
            prompt += "\n\nWhy the author made changes beyond the assignment text (validator failures it had to fix):\n" + "\n".join(
                f"- {failure['kind']}: {failure['detail']}" for failure in subject["failures"][-3:]
            ) + "\nChanges that fix these failures are in scope.\n"
        misfit = self._context_misfit(selection["provider"], prompt)
        if misfit:
            # Would be rejected by the model (live: a 64k window got a ~110k-token request
            # three times). Route elsewhere now instead of spending attempts.
            node.setdefault("excluded_providers", []).append(selection["provider"])
            node["state"] = "RUNNABLE"
            node["wait_reason"] = misfit
            self.store.append_event(record["run_id"], "context.misfit", node["id"], misfit)
            return False
        prompt_path = worker_dir / "prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        node["prompt_chars"] = len(prompt)
        run_id = record["run_id"]
        self.ledger.emit(
            run_id, "routing_decision", node["id"], role=node["role"], tier=_tier(selection["capability_class"]),
            capability_class=selection["capability_class"], requested=f"{node['requested_capability_class']}/{node['requested_effort']}",
            provider=selection["provider"], model=selection["model"], effort=selection["provider_effort"],
            escalations=node["escalations"], attempt=attempt, overridden=bool(selection.get("overridden")),
            reason=_routing_reason(node, selection),
        )
        self.ledger.emit(run_id, "model_selected", node["id"], role=node["role"], provider=selection["provider"], model=selection["model"], effort=selection["provider_effort"], capability_class=selection["capability_class"])
        if context:
            candidate = context.get("candidate_tokens_estimate") or 0
            chosen = context.get("selected_tokens_estimate") or 0
            self.ledger.emit(
                run_id, "context_selected", node["id"], **context,
                reduction_pct=round(100.0 * (candidate - chosen) / candidate, 1) if candidate else None,
                prompt_chars=len(prompt), diff_chars=len(diff or ""),
            )
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
        self.ledger.emit(record["run_id"], "review_started" if node["role"] == "reviewer" else "model_started", node["id"], role=node["role"], provider=selection["provider"], model=selection["model"], subject=node.get("subject"))
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
            subject = f"agent-os {record['run_id']}: integrate {node_id}"
            landed = manager.find_integration_commit(subject)
            if landed:
                # Idempotency: the merge already landed (e.g. the process died
                # after merging but before saving). Adopt it; never merge twice.
                node["integrated"] = True
                node["integration"] = {"commit": landed, "at": now(), "recovered": True}
                record["integration"]["head"] = manager.integration_head()
                if node_id not in record["integration"]["merged"]:
                    record["integration"]["merged"].append(node_id)
                self._release_claim(record, node, "integrated (recovered)")
                self.store.append_event(record["run_id"], "integration.recovered", node_id, landed[:12])
                continue
            outcome = manager.merge(node["worktree"]["branch"], subject)
            if outcome["merged"]:
                node["integrated"] = True
                node["integration"] = {"commit": outcome["commit"], "at": now()}
                record["integration"]["head"] = outcome["commit"]
                record["integration"]["merged"].append(node_id)
                self._release_claim(record, node, "integrated")
                self.store.append_event(record["run_id"], "integration.merged", node_id, outcome["commit"][:12])
                self.ledger.emit(record["run_id"], "commit_created", node_id, commit=outcome["commit"][:12], branch=record["integration"]["branch"])
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
        validation = self._validate(record, None, validators, integration["path"])
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
        self.ledger.emit(record["run_id"], "run_completed", integrated=len(merged), branch=integration["branch"])

    def _recover_landing(self, record: dict[str, Any]) -> bool:
        """Finish a landing whose approval was persisted but whose outcome was
        not (crash after the base branch moved). _land is an expected-value
        fast-forward, so running it again is a no-op when it already landed."""
        landing = (record.get("final") or {}).get("landing") or {}
        if landing.get("state") != "intended" or (record.get("final") or {}).get("landed"):
            return False
        try:
            self._land(record)
        except GitError as exc:
            record["final"]["landed"] = {"ok": False, "reason": redact(exc, 300)}
        landing["state"] = "recovered"
        self.store.append_event(record["run_id"], "landing.recovered", None, str((record["final"].get("landed") or {}).get("ok")))
        self._finish(record)
        self._derive_state(record)
        return True

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
        from .simple import GATE_CARDS

        self.ledger.emit(record["run_id"], "approval_required", node_id, gate=gate["id"], kind=kind, title=GATE_CARDS.get(kind, {}).get("title", "a decision").lower())
        if kind == "budget_exhausted":
            self.ledger.emit(record["run_id"], "loop_guard", node_id, guard="launch_budget", reason=gate["reason"])
        return gate

    def _defer_host_action(self, record: dict[str, Any], node: dict[str, Any], action: str) -> None:
        """Set aside a step only the host can do, without asking a person.

        Nothing from the step is merged; dependents proceed and the deferral is
        recorded so the final summary and handoff still name the host action."""
        node["state"] = "PASSED"
        node["completed_at"] = now()
        node["integrated"] = True
        node["integration"] = {"deferred": True, "reason": redact(action, 300), "at": now()}
        node["wait_reason"] = f"deferred host action: {redact(action, 200)}"
        record.setdefault("deferred_host_actions", []).append({"node": node["id"], "action": redact(action, 300), "at": now()})
        self._close_node_gates(record, node["id"], "deferred automatically: host-level action")
        self._release_claim(record, node, "deferred host action")
        self.store.append_event(record["run_id"], "node.deferred", node["id"], redact(action, 300))
        self.ledger.emit(record["run_id"], "loop_guard", node["id"], guard="host_action_deferred", reason="the step needs a host-level action, so it was deferred instead of opening a gate")

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
            _push_failure(
                node,
                "merge_conflict",
                (node.get("selection") or {}).get("provider"),
                gate["reason"],
                node.get("capability_class"),
            )
            node["state"] = "FAILED_RETRYABLE"
            node["selection"] = None
            node["retries"] = 0
            for other_id in list(record["order"]):
                other = record["nodes"][other_id]
                if other.get("subject") == node["id"] and other["state"] in DISPATCHABLE_NODE_STATES:
                    other["state"] = "CANCELLED"
        elif kind == "agent_needs_decision" and _host_action(gate.get("reason") or ""):
            self._defer_host_action(record, node, gate.get("reason") or "")
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
            deploying = [node for node in waiting if node["role"] == "planner" and str(node.get("wait_reason") or "").startswith("waiting for the session foreman")]
            resetting = [node for node in waiting if str(node.get("wait_reason") or "").startswith(USAGE_RESET_WAIT)]
            if deploying:  # not blocked: the foreman deployment finishes or falls back on its own
                state, reason = "PLANNING", deploying[0]["wait_reason"]
            elif resetting and not any(node["state"] in {"WAITING_FOR_REVIEW", "NEEDS_REPAIR"} for node in nodes):
                # Not blocked either: usage comes back on its own; the driver sleeps until then.
                state, reason = "READY", resetting[0]["wait_reason"]
            elif after_dispatch and waiting and not any(node["state"] in {"WAITING_FOR_REVIEW", "NEEDS_REPAIR"} for node in nodes):
                state, reason = "BLOCKED", "no runnable work: " + "; ".join(f"{node['id']}: {node['wait_reason']}" for node in waiting)[:600]
            elif any(node["state"] == "PASSED" and node["role"] in INTEGRATED_ROLES and not node["integrated"] for node in nodes):
                state, reason = "INTEGRATING", None
            else:
                state, reason = "READY", None
        if state != record["state"]:
            self.store.append_event(record["run_id"], "run.state", None, f"{record['state']} -> {state}")
            if state in {"BLOCKED", "FAILED"}:
                self.ledger.emit(record["run_id"], "run_failed", reason=redact(reason or state, 300))
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
            "origin": record.get("origin") or {"kind": "task"},
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
            "operator_messages": record.get("operator_messages", [])[-50:],
            "nodes": [_node_view(nodes[node_id]) for node_id in record["order"]],
            "telemetry_warning": self.ledger.warning(record["run_id"]),
        }

    def status(self, run_id: str) -> dict[str, Any]:
        return self.summary(self.store.load(run_id))

    def efficiency(self, run_id: str) -> dict[str, Any]:
        """Efficiency summary from the run's telemetry file, reconciled with
        the run record's own usage totals."""
        from .ledger import summarize

        events, malformed = self.ledger.read(run_id)
        report = summarize(events, malformed)
        try:
            record = self.store.load(run_id)
        except (KeyError, ValueError):
            record = None
        if record is not None:
            recorded = record.get("usage") or {}
            exact = report["tokens"]["exact"]
            report["reconciliation"] = {
                "run_record_exact_input_tokens": recorded.get("input_tokens"),
                "telemetry_exact_input_tokens": exact["input"] + report["tokens"]["synthetic"]["input"],
                "run_record_output_tokens": recorded.get("output_tokens"),
                "telemetry_output_tokens": exact["output"] + report["tokens"]["synthetic"]["output"],
                "consistent": recorded.get("input_tokens") == exact["input"] + report["tokens"]["synthetic"]["input"]
                and recorded.get("output_tokens") == exact["output"] + report["tokens"]["synthetic"]["output"],
            }
        report["telemetry_warning"] = self.ledger.warning(run_id)
        report["files"] = {name: str(path) for name, path in zip(("events", "transcript"), self.ledger.paths(run_id))}
        return report

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


def _hard_scope(node: dict[str, Any]) -> list[str]:
    """Scope that decides parallelism: without paths added only because the
    task's validator runs them (planner soft_scope). An empty result keeps the
    original scope, since an empty scope means the whole repository."""
    soft = set(node.get("soft_scope") or [])
    hard = [path for path in node.get("scope") or [] if path not in soft]
    return hard or list(node.get("scope") or [])


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


# Provider health lives in provider_health.py so delegate/eval share it
# (IMP-0005); these aliases keep the engine's existing names.
from . import provider_health as _health  # noqa: E402

_cooldown_path = _health.cooldown_path
_quota_reset = _health.quota_reset
_read_cooldowns = _health.read
_write_cooldown = _health.write_cooldown
_cooling_providers = _health.cooling


_HOST_ACTION_PATTERN = (
    r"\brestart(?:ing|ed)?\b.{0,40}\b(?:mcp|server|client|host|agent os)\b"
    r"|\b(?:mcp|agent os) server\b.{0,40}\brestart"
    r"|\b(?:mcp|host|server|client) restart"
    r"|\bhost[- ]level\b|\bhost operator\b|\bowning (?:mcp )?host\b|\bnested (?:agent os )?orchestrat"
)


def _host_action(text: str) -> bool:
    """Whether a worker's question is a host-level prerequisite rather than a
    design decision: no answer through a gate lets a sandboxed worker do it."""
    import re

    return bool(re.search(_HOST_ACTION_PATTERN, text or "", re.IGNORECASE))


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


def _push_failure(
    node: dict[str, Any], kind: str, provider: str | None, detail: str, capability_class: str | None = None
) -> None:
    node["failures"].append(
        {
            "kind": kind,
            "provider": provider,
            "capability_class": capability_class,
            "detail": redact(detail, 300),
            "at": now(),
        }
    )
    del node["failures"][:-MAX_FAILURES_KEPT]


def _evidence_line(validation: dict[str, Any]) -> str:
    parts = []
    for item in validation.get("evidence", []):
        status = "ok" if item["passed"] else "FAIL"
        parts.append(f"{item.get('name')}={status}" + (f" ({item['detail']})" if not item["passed"] and item.get("detail") else ""))
    return redact("; ".join(parts) or "no validators", 400)


_TIERS = {"deterministic": "local", "fast": "cheap/fast model", "balanced": "stronger model", "reasoning": "high-reasoning model", "frontier": "highest-capability model"}


def _tier(capability_class: str | None) -> str:
    return _TIERS.get(str(capability_class), str(capability_class))


def _routing_reason(node: dict[str, Any], selection: dict[str, Any]) -> str:
    """Why this tier, then why this provider: one plain sentence."""
    requested = node["requested_capability_class"]
    if selection.get("overridden"):
        why = "you set an override"
    elif node["escalations"]:
        why = f"escalated {node['escalations']} step(s) from {requested} after failed validation"
    elif node["role"] == "reviewer":
        why = "reviews use at least the balanced tier and a different provider from the author"
    elif node["role"] == "planner":
        why = "planning uses the run's planner tier; a better plan saves more than it costs"
    elif node["role"] == "repairer":
        why = "repairs run at the task's planned tier unless the findings are critical/high"
    else:
        why = f"planned as {requested} work"
    return f"{why}; {selection.get('reason') or 'router default'}"


def _tree_hash(cwd: str | Path) -> str | None:
    from .worktrees import git

    try:
        completed = git(["rev-parse", "HEAD^{tree}"], cwd, check=False)
    except Exception:
        return None
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else None


def _validation_key(tree: str, validators: list[dict[str, Any]]) -> str:
    import hashlib
    import json

    return hashlib.sha256(json.dumps([tree, validators], sort_keys=True, default=str).encode("utf-8")).hexdigest()[:24]


def _test_totals(evidence: list[dict[str, Any]]) -> dict[str, int | None]:
    counted = [item for item in evidence if "tests_run" in item]
    if not counted:
        return {"tests_run": None, "tests_passed": None, "tests_failed": None}
    return {key: sum(int(item.get(key) or 0) for item in counted) for key in ("tests_run", "tests_passed", "tests_failed")}


_SNAPSHOT_SKIP = ("stdout.log", "stderr.log", "driver.json", "driver.log", "driver.lock")


def _snapshot_run_history(home: Path | str, cwd: Path | str) -> Path:
    """Copy this machine's run history (without raw worker logs) into the
    worker's git-ignored ``.agent-local`` (policy share_run_history).

    Every worker can read its own worktree whatever its sandbox (some agent
    CLIs refuse paths outside it), and a copy cannot disturb the live runs."""
    import shutil

    source = Path(home) / "runs"
    target_home = Path(cwd) / ".agent-local" / "orchestrator"
    if source.is_dir():
        shutil.copytree(source, target_home / "runs", ignore=shutil.ignore_patterns(*_SNAPSHOT_SKIP), dirs_exist_ok=True)
    return target_home


def _run_history_note(snapshot_home: Path | str) -> str:
    """Tell the worker where its snapshot of the run history is."""
    from .store import HOME_ENV

    return (
        "\n\nRun history of this machine (a snapshot copied for you; evidence only, do not start or control runs):\n"
        "- files: .agent-local/orchestrator/runs/<run-id>/ in your working directory (state.json, events.jsonl,\n"
        "  telemetry.jsonl, workers/<node>-<attempt>/prompt.md and last-message.md)\n"
        f"- CLI: set {HOME_ENV}={snapshot_home} for `python -m agent_os orchestrate list|status|events|report|usage-report|context-anatomy`\n"
    )


USAGE_RESET_WAIT = "waiting for usage reset:"
# Consecutive git/OS tick failures the driver rides out (5s, 10s, 20s ... backoff)
# before giving up; one killed git child must not orphan a long run.
TRANSIENT_TICK_RETRIES = 6
# Floor for the driver's wait between ticks when no worker is running.
IDLE_TICK_SECONDS = 5.0


def _operator_changed(record: dict[str, Any]) -> None:
    """Mark an operator control change so a driver process that loaded the
    run earlier adopts it instead of saving over it (RunStore.refresh_control)."""
    record["control"]["rev"] = int(record["control"].get("rev") or 0) + 1


def _prior_attempts(node: dict[str, Any], severities: list[str] | None = None) -> str:
    lines = []
    unresolved = material((node.get("review") or {}).get("findings") or [], severities or ["critical", "high", "medium"]) if node.get("role", "implementer") in {"implementer", "test_author"} else []
    for failure in node["failures"][-3:]:
        lines.append(f"- previous attempt: {failure['kind']}: {failure['detail']}")
    for decision in node.get("decisions", [])[-3:]:
        lines.append(f"- operator decision: {decision}")
    for item in unresolved[-8:]:
        lines.append(f"- unresolved review finding [{item['id']}] {item['severity']} {item.get('path') or ''}: {str(item['summary'])[:300]}")
    if unresolved:
        # A retry after a rejected review gate otherwise sees the reviewed
        # work in its worktree and reports it already_done unchanged.
        lines.append("- a review rejected the work in your worktree for the findings above. Do not report already_done: fix each one, then report done.")
    if not lines:
        return ""
    if node["failures"] and node["failures"][-1]["kind"] == "validator_failed":
        # A retried worker otherwise sees the earlier work in its worktree,
        # reports already_done, and fails the same validator again.
        lines.append(
            "- the work in your worktree FAILS validation. Do not report already_done: fix the failure named above"
            " (run that test to see why), then report done."
        )
    return "\n\nContext from earlier attempts on this assignment (your worktree keeps their partial work):\n" + "\n".join(lines) + "\n"


def _node_view(node: dict[str, Any]) -> dict[str, Any]:
    selection = node.get("selection") or {}
    worktree = node.get("worktree") or {}
    return {
        "id": node["id"],
        "role": node["role"],
        "goal": node["goal"][:240],
        "started_at": (node.get("process") or {}).get("started_at"),
        "state": node["state"],
        "wait_reason": node.get("wait_reason"),
        "subject": node.get("subject"),
        "depends_on": node["depends_on"],
        "scope": node["scope"],
        "capability_class": node["capability_class"],
        "requested_capability_class": node["requested_capability_class"],
        "effort": node["effort"],
        "execution_path": node["execution_path"],
        "preferred_execution_path": node.get("preferred_execution_path", node["execution_path"]),
        "available_execution_paths": node.get("available_execution_paths", [node["execution_path"]]),
        "execution_route": node.get("execution_route"),
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
        "excluded_classes": node.get("excluded_classes", {}),
        "failures": node["failures"][-3:],
        "validation": node.get("validation"),
        "review": node["review"],
        "integrated": node["integrated"],
        "checkpoint": node.get("checkpoint"),
        "result": node.get("result"),
    }


def _control_plane(record: dict[str, Any], node: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Protected control/evaluation plane settings for this run, or None when
    the run targets another repository (control_plane.applies_to). With a node,
    the worktree base commit enables the negative-evidence append-only check."""
    from .control_plane import applies_to

    if not applies_to(record.get("repository"), record.get("project")):
        return None
    base = ((node or {}).get("worktree") or {}).get("base_commit")
    return {"allowed": list(record["policy"].get("protected_paths_allowed") or []), "base_commit": base}


def _publication_guard(record: dict[str, Any], node: dict[str, Any]) -> dict[str, Any] | None:
    """IMP-0014: every orchestrated editing node (any repository) fails
    validation when its worker transcript shows an attempted external
    publication, unless the operator allowed it in run policy."""
    from .control_plane import publication_check

    if record["policy"].get("allow_worker_publication"):
        return None
    process = node.get("process") or {}
    paths = [process.get("stdout_path")] if process.get("stdout_path") else []
    return publication_check(paths) if paths else None
