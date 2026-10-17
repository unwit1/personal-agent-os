"""Failure learning: every model failure is a defect to remove, not noise.

Policy ``failure_learning`` (orchestrator-os.policy.json, ``failure_learning``):

1. Remedy in the run. Known failure patterns already have a deterministic
   remedy inside the run (``REMEDIES``): the retry quotes the failing output,
   denied commands do not park finished work, a refusal fails over to another
   model, reviewer flip-flops stop early, and so on.
2. Record. When a run's driver stops, every failure in it gets a normalised
   signature (``signatures``), appended once to
   ``<home>/failure-signatures.jsonl``.
3. Improve. A signature with no remedy, or one that recurs in at least
   ``failure_learning_repeat_runs`` runs within ``WINDOW_DAYS`` despite its
   remedy, becomes an improvement record (IMP), deduplicated per signature.
4. Fix. In mode ``fix`` (default) each new or reopened improvement starts a
   fix run against Agent OS itself at once: planned, validated and reviewed
   like any run, capped by ``failure_learning_fix_max_usd`` and
   ``failure_learning_daily_fix_runs``, never touching protected paths, and
   left on a branch: merging to the default branch still needs approval
   (constitution, approval_required_for). A fix run never starts another.

Signatures are deterministic text: no model call is made to classify.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

MODES = ("off", "record", "improve", "fix")
WINDOW_DAYS = 30
# Operational events, not defects: a usage limit, a user cancel, a lost process.
IGNORED_KINDS = frozenset({"quota", "cancelled", "interrupted"})
TERMINAL_STATES = frozenset({"COMPLETE", "FAILED", "CANCELLED"})

# Signature prefix -> the remedy that already acts inside a run. A signature
# with a remedy is only escalated to an improvement when it keeps recurring.
REMEDIES: dict[str, str] = {
    "validator_failed:": "retry prompt quotes the failing validator output (validators.failure_excerpt)",
    "validator_failed:unchanged": "retry prompt says the failing output did not change",
    "permission_denied:": "editing workers may run their validators and read-only commands (engine._worker_allowed_tools)",
    "blocked_on_host:deferred": "blocked_on_host with changed files is validated instead of deferred; only a step that changed nothing is deferred",
    "refused": "refusal is recorded and the node fails over to another model class",
    "review_oscillation": "repair that restores a reviewed version stops the cheap review loop",
    "review_unresolved": "after the extra repair, late medium-or-lower findings no repair was asked to fix become follow-ups instead of a gate (engine._after_blocking_review)",
    "invalid_model": "the provider/class is excluded for the node and the model learned as unavailable",
    "unavailable": "provider breaker opens after repeated unavailability",
    "process_error": "provider failover after repeated process errors on the node",
    "escalated:": "escalation ladder (stronger tier after failed attempts)",
}


def remedy_for(signature: str) -> str | None:
    best = None
    for prefix, remedy in REMEDIES.items():
        if (signature == prefix or (prefix.endswith(":") and signature.startswith(prefix))) and (best is None or len(prefix) > len(best[0])):
            best = (prefix, remedy)
    return best[1] if best else None


_ERROR_TYPE = re.compile(r"\b([A-Z][A-Za-z]*(?:Error|Exception))\b")


def _error_type(text: str) -> str:
    match = _ERROR_TYPE.search(text or "")
    return match.group(1) if match else "tests"


def _program(command: str) -> str:
    words = str(command).replace("&&", " ").split()
    return " ".join(words[:2]) if words else "?"


def signatures(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Every failure in the run as {key, signature, node, role, model, detail}.

    ``key`` is stable per occurrence, so learning the same run twice records
    nothing new."""
    found: list[dict[str, Any]] = []

    def add(node: dict[str, Any], key: str, signature: str, detail: str) -> None:
        selection = node.get("selection") or {}
        found.append({"key": f"{node['id']}|{key}", "signature": signature, "node": node["id"], "role": node.get("role"),
                      "provider": selection.get("provider"), "model": selection.get("model"), "detail": str(detail or "")[:240]})

    for node in record.get("nodes", {}).values():
        failures = node.get("failures") or []
        for index, failure in enumerate(failures):
            kind = failure.get("kind") or "unknown"
            if kind in IGNORED_KINDS:
                continue
            detail = failure.get("detail") or ""
            if kind == "validator_failed":
                previous = failures[index - 1] if index else {}
                if "editable-scope=FAIL" in detail:
                    signature = "scope_violation"
                elif previous.get("kind") == "validator_failed" and failure.get("excerpt") and failure.get("excerpt") == previous.get("excerpt"):
                    signature = "validator_failed:unchanged"
                else:
                    signature = f"validator_failed:{_error_type(failure.get('excerpt') or detail)}"
            else:
                signature = kind
            add(node, f"failure{index}", signature, detail)
        result = node.get("result") or {}
        signals = result.get("signals") or {}
        for command in signals.get("denied_commands") or []:
            add(node, f"denied{node.get('attempts')}:{_program(command)}", f"permission_denied:{_program(command)}", command)
        integration = node.get("integration") or {}
        if integration.get("deferred"):
            add(node, "deferred", "blocked_on_host:deferred", integration.get("reason") or "")
        review = node.get("review") or {}
        if review.get("oscillation"):
            add(node, "oscillation", "review_oscillation", "a repair restored an already-reviewed version")
        if node.get("escalations"):
            add(node, f"escalated{node['escalations']}", f"escalated:{node.get('role')}", f"{node['escalations']} escalation(s); now {node.get('capability_class')}")
        if node.get("state") == "FAILED_FINAL":
            reason = node.get("wait_reason") or ""
            if failures:
                signature = f"failed_final:{failures[-1]['kind']}"
            else:
                signature = "unroutable" if "provider" in reason.lower() else "failed_final:unknown"
            add(node, "failed_final", signature, reason)
    for gate in record.get("gates") or []:
        if gate.get("kind") == "unresolved_review_findings":
            node = record["nodes"].get(gate.get("node") or "") or {"id": gate.get("node") or "?"}
            add(node, f"gate{gate.get('id')}", "review_unresolved", gate.get("reason") or "")
    return found


def ledger_path(home: Path) -> Path:
    return Path(home) / "failure-signatures.jsonl"


def fix_runs_path(home: Path) -> Path:
    return Path(home) / "failure-fix-runs.jsonl"


def _read(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows = []
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _append(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def summary(home: Path, days: int = WINDOW_DAYS) -> dict[str, Any]:
    """Signatures seen in the window: occurrences, distinct runs, remedy."""
    since = (_now() - timedelta(days=days)).isoformat()
    by: dict[str, dict[str, Any]] = {}
    for row in _read(ledger_path(home)):
        if str(row.get("at") or "") < since:
            continue
        item = by.setdefault(row["signature"], {"occurrences": 0, "runs": set(), "remedy": remedy_for(row["signature"]), "last": None})
        item["occurrences"] += 1
        item["runs"].add(row.get("run_id"))
        item["last"] = max(item["last"] or "", str(row.get("at") or ""))
    ranked = sorted(by.items(), key=lambda kv: (-len(kv[1]["runs"]), -kv[1]["occurrences"]))
    return {"window_days": days, "signatures": {key: {**value, "runs": len(value["runs"])} for key, value in ranked}}


def learn(home: Path, record: dict[str, Any], *, repeat_runs: int = 2) -> dict[str, Any]:
    """Record the run's new failures and return the signatures that need an
    improvement: those without a remedy, and those recurring in at least
    ``repeat_runs`` runs within the window despite one."""
    seen = set((record.get("failure_learning") or {}).get("seen") or [])
    new = [item for item in signatures(record) if item["key"] not in seen]
    at = _now().isoformat()
    _append(ledger_path(home), ({**item, "run_id": record["run_id"], "at": at} for item in new))
    record.setdefault("failure_learning", {})["seen"] = sorted(seen | {item["key"] for item in new})
    stats = summary(home)["signatures"]
    needs: dict[str, dict[str, Any]] = {}
    for item in new:
        signature = item["signature"]
        info = stats.get(signature) or {"runs": 1, "occurrences": 1}
        remedy = remedy_for(signature)
        if remedy is None or info["runs"] >= repeat_runs:
            entry = needs.setdefault(signature, {"signature": signature, "remedy": remedy, "runs": info["runs"],
                                                 "occurrences": info["occurrences"], "examples": []})
            if len(entry["examples"]) < 5:
                entry["examples"].append(f"{record['run_id']}/{item['node']} ({item.get('model') or 'local'}): {item['detail'][:160]}")
    return {"recorded": len(new), "needs_improvement": list(needs.values())}


def improvement_fields(need: dict[str, Any]) -> dict[str, Any]:
    """Arguments for improvements.capture_improvement, deduplicated per signature."""
    signature = need["signature"]
    remedy = need.get("remedy")
    if remedy:
        observation = (f"Failure signature {signature} recurred in {need['runs']} run(s) ({need['occurrences']} occurrence(s) "
                       f"in {WINDOW_DAYS} days) although a remedy exists: {remedy}.")
        direction = "Find why the existing remedy does not prevent it and make a deterministic change (code, prompt rule, validator or permission) that does."
    else:
        observation = f"Failure signature {signature} has no deterministic remedy yet ({need['occurrences']} occurrence(s) in {need['runs']} run(s))."
        direction = "Reproduce it from the run records, then add a deterministic remedy (code, prompt rule, validator or permission) and list it in failure_learning.REMEDIES."
    return {
        "title": f"Worker failure: {signature}",
        "category": "bug",
        "subsystem": "orchestrator",
        "priority": "high" if need["runs"] >= 3 or signature.startswith("failed_final") else "medium",
        "observation": observation,
        "suggested_direction": direction,
        "acceptance": [
            f"a regression test reproduces {signature} from a recorded case and passes with the fix",
            f"{signature} does not recur in the next runs (agent-os orchestrate learn --summary)",
        ],
        "evidence": need["examples"],
        "source": {"type": "regression", "reference": signature},
        "dedupe_key": f"failure-signature:{signature}",
    }


def fix_goal(improvement_id: str, need: dict[str, Any]) -> str:
    examples = "\n".join(f"- {line}" for line in need["examples"])
    remedy = f"Existing remedy that did not prevent it: {need['remedy']}." if need.get("remedy") else "There is no remedy yet."
    return (
        f"Fix orchestrator worker failure {need['signature']} ({improvement_id}). It occurred {need['occurrences']} time(s) in "
        f"{need['runs']} run(s). {remedy}\nExamples (run/node (model): detail):\n{examples}\n"
        "Make the smallest deterministic change in src/agent_os/orchestrator (code, worker prompt rule, permission or "
        "validator) that prevents this failure, add a regression test that reproduces it, and list the remedy in "
        "failure_learning.REMEDIES. Do not edit protected paths (policy/**, validators.py, review.py, eval.py, "
        "control_plane.py); if the fix needs one, report status needs_decision and say which."
    )


def fix_run_allowed(home: Path, signature: str, *, daily_limit: int, active_runs: Iterable[str]) -> str | None:
    """None when a fix run may start; otherwise the reason it may not."""
    rows = _read(fix_runs_path(home))
    today = _now().date().isoformat()
    if sum(1 for row in rows if str(row.get("at") or "").startswith(today)) >= daily_limit:
        return f"daily limit of {daily_limit} fix run(s) reached"
    active = set(active_runs)
    if any(row.get("signature") == signature and row.get("run_id") in active for row in rows):
        return "a fix run for this signature is still active"
    return None


def note_fix_run(home: Path, signature: str, run_id: str, improvement_id: str) -> None:
    _append(fix_runs_path(home), [{"at": _now().isoformat(), "signature": signature, "run_id": run_id, "improvement": improvement_id}])
