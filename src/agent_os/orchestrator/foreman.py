"""Shadow foreman: a candidate planner/router evaluated against the incumbent (IMP-0015).

Roadmap ("Abliterated / low-refusal foreman"): an optional model -- any
registered provider, including an open-weight or abliterated one -- may
propose a task DAG and routes, but only in **shadow mode** first:

1. the Orchestrator executes a run normally;
2. ``propose`` renders the run's goal and tasks as a neutral Task Context
   Contract and asks a foreman model (through ``delegate --role inline``,
   honouring workload requirements such as ``prefer_refusal_profile``) for a
   proposed DAG with a capability class per task;
3. the proposal is stored next to the run (``<home>/foreman-shadow/<run>/``)
   with its contract digest, route, usage and any refusal;
4. ``compare`` scores the proposal against what actually happened: class
   agreement, where a cheaper class would likely have sufficed (the incumbent
   passed first time without escalation) versus where it would likely have
   failed (the incumbent needed retries/escalation), DAG edge differences, and
   task coverage.

The foreman never gains routing authority here; promotion needs eval and
shadow evidence (DEC-0030, roadmap Phase 3). ``compare`` and ``report`` are
deterministic; ``propose`` is one real model call.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from ..capabilities import CAPABILITY_CLASSES, rank
from ..timestamps import utc_now_iso
from . import context_contract
from .store import orchestrator_home

TASK_FAMILY = "foreman_shadow"
PLANNED_ROLES = {"planner", "implementer", "test_author"}
OUTPUT_CONTRACT = {
    "required": {"tasks": "array"},
    "tasks": {"required": {"id": "string", "capability_class": "string"},
              "enums": {"capability_class": list(CAPABILITY_CLASSES)}, "min_items": 1},
}


def shadow_dir(run_id: str, home: Path | None = None) -> Path:
    return Path(home or orchestrator_home()) / "foreman-shadow" / run_id


def planned_nodes(record: dict[str, Any]) -> list[dict[str, Any]]:
    """The run's planned work (not reviewers/repairers the engine added)."""
    return [node for node_id in record.get("order", list(record["nodes"])) if (node := record["nodes"].get(node_id))
            and node.get("origin", "plan") == "plan" and node.get("role") in PLANNED_ROLES]


def build_contract(record: dict[str, Any], providers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    tasks = [{"id": node["id"], "goal": node["goal"][:600], "role": node["role"], "depends_on": node["depends_on"], "scope": node.get("scope")}
             for node in planned_nodes(record)]
    facts: list[Any] = [
        {"text": "This is a shadow evaluation: your proposal is recorded and compared, it is not executed.", "safety_relevant": True},
        f"Capability classes, cheapest first: {', '.join(item for item in CAPABILITY_CLASSES)}. 'deterministic' means no model is needed.",
    ]
    if providers:
        routes = [{"id": item["id"], "classes": sorted(item["models"]), "profile": {key: (item.get("profile") or {}).get(key) for key in ("deployment", "refusal_profile")}}
                  for item in providers]
        facts.append("Available routes: " + json.dumps(routes, sort_keys=True))
    return context_contract.build(
        f"Propose the cheapest reliable plan for this goal: {record.get('goal', '')[:800]}",
        facts=facts,
        constraints=[
            "Keep the given task ids; you may add depends_on edges or remove unnecessary ones.",
            "Pick the cheapest capability class you expect to pass validation on the first attempt.",
            "Explain each choice in one short reason.",
        ],
        inputs=[{"name": "tasks.json", "content": json.dumps(tasks, indent=1)}],
        output={"tasks": [{"id": "string", "depends_on": ["string"], "capability_class": "one of " + "/".join(CAPABILITY_CLASSES), "reason": "string"}]},
    )


def propose(run_id: str, *, provider: str | None = None, requirements: dict[str, Any] | None = None, home: Path | None = None,
            record_evidence: bool = True, registry=None, loader=None) -> dict[str, Any]:
    """Ask a foreman model for a proposal on an existing run and store it."""
    from .delegate import delegate
    from .router import ProviderRegistry
    from .store import RunStore

    record = (loader or RunStore(home).load)(run_id)
    registry = registry or ProviderRegistry()
    contract = build_contract(record, registry.providers)
    outcome = delegate(context_contract.render(contract), task_family=TASK_FAMILY, capability_class="balanced", effort="medium",
                       contract=OUTPUT_CONTRACT, provider=provider, role="inline", requirements=requirements, registry=registry,
                       home=home, record=record_evidence)
    proposal = {
        "id": f"FSH-{uuid.uuid4().hex[:10]}",
        "run_id": run_id,
        "at": utc_now_iso(),
        "contract_digest": contract["digest"],
        "omitted": contract["omitted"],
        "selection": outcome.get("selection"),
        "status": outcome.get("status"),
        "refusal": outcome.get("refusal"),
        "usage": outcome.get("usage"),
        "delegation": outcome.get("id"),
        "proposal": outcome.get("result"),
    }
    target = shadow_dir(run_id, home)
    target.mkdir(parents=True, exist_ok=True)
    (target / f"{proposal['id']}.json").write_text(json.dumps(proposal, indent=1), encoding="utf-8")
    return proposal


def _incumbent(node: dict[str, Any]) -> dict[str, Any]:
    selection = node.get("selection") or {}
    usage = (node.get("result") or {}).get("usage") or {}
    return {
        "requested_class": node.get("requested_capability_class") or node.get("capability_class"),
        "final_class": selection.get("capability_class") or node.get("capability_class"),
        "provider": selection.get("provider"),
        "attempts": int(node.get("attempts") or 0),
        "retries": int(node.get("retries") or 0),
        "escalations": int(node.get("escalations") or 0),
        "passed": node.get("state") == "PASSED" or bool(node.get("integrated")),
        "cost_usd": usage.get("cost_usd"),
    }


def compare(record: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    """Deterministic score of one proposal against the run's actual outcome."""
    proposed = {str(item.get("id")): item for item in ((proposal.get("proposal") or {}).get("tasks") or []) if isinstance(item, dict)}
    rows, counts = [], {"agree": 0, "cheaper_likely_ok": 0, "cheaper_risky": 0, "stronger": 0, "unscored": 0}
    edges_missing, edges_extra = [], []
    nodes = planned_nodes(record)
    for node in nodes:
        actual = _incumbent(node)
        item = proposed.get(node["id"])
        if not item or item.get("capability_class") not in CAPABILITY_CLASSES:
            counts["unscored"] += 1
            rows.append({"id": node["id"], "verdict": "unscored", "incumbent": actual})
            continue
        wanted = item["capability_class"]
        base = actual["final_class"] if actual["final_class"] in CAPABILITY_CLASSES else actual["requested_class"]
        clean_first_try = actual["passed"] and actual["attempts"] <= 1 and not actual["retries"] and not actual["escalations"]
        if wanted == base:
            verdict = "agree"
        elif rank(wanted) < rank(base):
            verdict = "cheaper_likely_ok" if clean_first_try else "cheaper_risky"
        else:
            verdict = "stronger"
        counts[verdict] += 1
        mine = set(str(dep) for dep in item.get("depends_on") or [])
        theirs = set(node["depends_on"])
        edges_missing += [f"{dep}->{node['id']}" for dep in sorted(theirs - mine)]
        edges_extra += [f"{dep}->{node['id']}" for dep in sorted(mine - theirs)]
        rows.append({"id": node["id"], "verdict": verdict, "proposed_class": wanted, "incumbent": actual, "reason": str(item.get("reason") or "")[:200]})
    scored = len(nodes) - counts["unscored"]
    return {
        "run_id": record.get("run_id"),
        "proposal_id": proposal.get("id"),
        "foreman": (proposal.get("selection") or {}).get("provider"),
        "foreman_model": (proposal.get("selection") or {}).get("model"),
        "foreman_status": proposal.get("status"),
        "foreman_refusal": proposal.get("refusal"),
        "tasks": len(nodes),
        "scored": scored,
        "class_agreement": round(counts["agree"] / scored, 3) if scored else None,
        "counts": counts,
        "extra_tasks": sorted(set(proposed) - {node["id"] for node in nodes}),
        "dag": {"edges_missing": edges_missing, "edges_extra": edges_extra},
        "rows": rows,
    }


def load_proposals(run_id: str, home: Path | None = None) -> list[dict[str, Any]]:
    target = shadow_dir(run_id, home)
    out = []
    for path in sorted(target.glob("FSH-*.json")) if target.exists() else []:
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except ValueError:
            continue
    return out


def report(home: Path | None = None, loader=None) -> dict[str, Any]:
    """Aggregate every stored proposal against its run."""
    from .store import RunStore

    root = Path(home or orchestrator_home()) / "foreman-shadow"
    load = loader or RunStore(home).load
    per_foreman: dict[str, dict[str, Any]] = {}
    comparisons = []
    for run_dir in sorted(root.iterdir()) if root.exists() else []:
        try:
            record = load(run_dir.name)
        except Exception:
            continue
        for proposal in load_proposals(run_dir.name, home):
            result = compare(record, proposal)
            comparisons.append({key: result[key] for key in ("run_id", "proposal_id", "foreman", "foreman_status", "class_agreement", "counts")})
            key = f"{result['foreman']}/{result['foreman_model']}"
            bucket = per_foreman.setdefault(key, {"proposals": 0, "refusals": 0, "scored": 0, "agree": 0, "cheaper_likely_ok": 0, "cheaper_risky": 0, "stronger": 0})
            bucket["proposals"] += 1
            bucket["refusals"] += 1 if result["foreman_refusal"] else 0
            bucket["scored"] += result["scored"]
            for name in ("agree", "cheaper_likely_ok", "cheaper_risky", "stronger"):
                bucket[name] += result["counts"][name]
    return {"foremen": per_foreman, "comparisons": comparisons,
            "note": "shadow only: no routing authority; promotion needs eval + shadow evidence (roadmap Phase 3)"}
