"""Task-specific capability evidence (CAP records).

Observations are raw, per-call, machine-local and append-only
(``<orchestrator home>/capability/observations.jsonl``, default ``.agent-local/orchestrator``). They carry no
prompt or output text. ``summarize`` aggregates them by

    task family x role x provider x concrete model x effort x toolset

into CAP records with a sample count, validator pass rate, a Wilson 95%
interval, latency, tokens and cost per *successful* task. ``write_records``
stores those aggregates in Git (``projects/personal-agent-os/orchestrator-os/
records/capability/``), which is the durable, provider-neutral evidence the
router may later consult. Tiny samples stay labelled by their interval; a
cheap route is only "qualified" for a family when the interval's lower bound
clears the family's reliability floor (policy ``routing.reliability_floor``).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from ..paths import ROOT
from ..timestamps import utc_now_iso
from .store import orchestrator_home

# Provider availability failures say nothing about capability: they are counted
# separately and excluded from the pass rate.
AVAILABILITY_FAILURES = ("quota", "unavailable", "auth", "rate_limit")
KEY_FIELDS = ("task_family", "role", "provider", "model_resolved", "effort", "toolset")
RECORDS_DIR = ROOT / "projects" / "personal-agent-os" / "orchestrator-os" / "records" / "capability"


def observations_path(home: Path | None = None) -> Path:
    return Path(home or orchestrator_home()) / "capability" / "observations.jsonl"


def record_observation(observation: dict[str, Any], *, home: Path | None = None) -> None:
    path = observations_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(observation, sort_keys=True) + "\n")


def read_observations(home: Path | None = None) -> list[dict[str, Any]]:
    try:
        lines = observations_path(home).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    result = []
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            result.append(item)
    return result


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if n <= 0:
        return None, None
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)


def _mean(values: Iterable[Any]) -> float | None:
    numbers = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    return round(sum(numbers) / len(numbers), 2) if numbers else None


def cap_id(key: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps([key.get(field) for field in KEY_FIELDS]).encode()).hexdigest()[:10]
    return f"CAP-{digest}"


def summarize(observations: list[dict[str, Any]], floor: float = 0.9) -> list[dict[str, Any]]:
    groups: dict[tuple, list[dict[str, Any]]] = {}
    for item in observations:
        if item.get("status") == "unroutable":
            continue
        key = tuple(item.get(field) or item.get("model") if field == "model_resolved" else item.get(field) for field in KEY_FIELDS)
        groups.setdefault(key, []).append(item)
    records = []
    for key, items in sorted(groups.items(), key=lambda pair: [str(part) for part in pair[0]]):
        identity = dict(zip(KEY_FIELDS, key))
        blocked = [item for item in items if str(item.get("failure_type") or "").startswith(AVAILABILITY_FAILURES)]
        items = [item for item in items if item not in blocked]
        if not items:
            records.append({"schema": "personal-agent/evidence-record/v1", "id": cap_id(identity), "type": "CAP", "title": f"{identity['task_family']} via {identity['provider']}/{identity['model_resolved']} ({identity['effort']}) -- no capability samples", "status": "active", "key": identity, "metrics": {"sample_count": 0, "availability_failures": len(blocked)}, "links": [], "provenance": {"source": "agent-os orchestrate capability --write"}, "updated_at": utc_now_iso()})
            continue
        # Accuracy-scored observations (orchestrate eval) supersede contract-only
        # ones for the pass rate; contract_pass_rate still covers every sample.
        contract_only = [item for item in items if item.get("accuracy") is None]
        scored = [item for item in items if item.get("accuracy") is not None]
        all_items, items = items, scored or items
        n = len(items)
        passed = [item for item in items if item.get("validator_passed")]
        low, high = wilson(len(passed), n)
        costs = [item.get("cost_usd") for item in items if isinstance(item.get("cost_usd"), (int, float))]
        failures: dict[str, int] = {}
        for item in items:
            if not item.get("validator_passed"):
                label = str(item.get("failure_type") or "unknown").split(":")[0][:60]
                failures[label] = failures.get(label, 0) + 1
        records.append({
            "schema": "personal-agent/evidence-record/v1",
            "id": cap_id(identity),
            "type": "CAP",
            "title": f"{identity['task_family']} via {identity['provider']}/{identity['model_resolved']} ({identity['effort']})",
            "status": "active",
            "key": identity,
            "metrics": {
                "sample_count": n,
                "final_success": len(passed),
                "validator_pass_rate": round(len(passed) / n, 3),
                "pass_rate_wilson95": [low, high],
                "qualified_at_floor": floor if low is not None and low >= floor else None,
                # Item-level accuracy on labeled cases (orchestrate eval); None
                # when only the output contract was checked (FND-0001).
                "mean_accuracy": _mean(item.get("accuracy") for item in items),
                "contract_pass_rate": round(sum(1 for item in all_items if item.get("contract_passed", item.get("validator_passed"))) / len(all_items), 3),
                "pass_basis": "accuracy_vs_labels" if scored else "output_contract",
                "contract_only_samples": len(contract_only) if scored else 0,
                "repairs": sum(int(item.get("repairs") or 0) for item in items),
                "mean_seconds": _mean(item.get("seconds") for item in items),
                "mean_input_tokens": _mean(item.get("input_tokens") for item in items),
                "mean_output_tokens": _mean(item.get("output_tokens") for item in items),
                "total_cost_usd": round(sum(costs), 6) if costs else None,
                "cost_per_success_usd": round(sum(costs) / len(passed), 6) if costs and passed else None,
                "failure_clusters": failures,
                "availability_failures": len(blocked),
            },
            "links": [{"rel": "derived_from", "ref": f"local:capability/observations.jsonl#{item.get('call_id')}"} for item in all_items][-20:],
            "provenance": {"source": "agent-os orchestrate capability --write", "observed_from": min(i.get("at") or "" for i in items), "observed_to": max(i.get("at") or "" for i in items)},
            "updated_at": utc_now_iso(),
        })
    return records


def write_records(records: list[dict[str, Any]], directory: Path | None = None) -> list[str]:
    target = Path(directory or RECORDS_DIR)
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for record in records:
        path = target / f"{record['id']}.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
        written.append(str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path))
    return written


def load_records(directory: Path | None = None) -> list[dict[str, Any]]:
    target = Path(directory or RECORDS_DIR)
    records = []
    for path in sorted(target.glob("CAP-*.json")):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return records
