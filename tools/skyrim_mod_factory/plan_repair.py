#!/usr/bin/env python3
"""Build a bounded Skyrim Mod Factory repair plan from a bug/failure record.

Known analyzer rules are the authority for fix mode. Unknown failures remain
proposal/manual work until a reproducible root cause and validator exist.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_HANDLER_REGISTRY = REPO / "knowledge/libraries/skyrim-modding/automation/repair-handler-registry.json"

MODE_MAP = {
    "automatic": "automatic",
    "proposal": "proposal",
    "manual": "manual",
    "none": "forbidden",
}

LAYER_VALIDATORS = {
    "plugin": ["mutagen", "xdump", "xedit"],
    "records": ["mutagen", "xdump", "xedit"],
    "papyrus": ["official-papyruscompiler", "caprica", "papyrus-utility"],
    "native": ["build-matrix", "devbench", "crash-logger"],
    "mesh": ["pynifly", "nifskope"],
    "texture": ["directxtex", "asset-closure"],
    "behavior": ["pandora", "runtime-test"],
    "animation": ["pandora", "runtime-test"],
    "navmesh": ["xedit", "ckpe", "runtime-test"],
    "world": ["xdump", "xedit", "runtime-test"],
    "dialogue": ["xdump", "xedit", "runtime-test"],
    "voice": ["asset-closure", "runtime-test"],
    "generated-output": ["generator-readback", "xdump"],
    "validation": ["independent-denominator-check"],
    "runtime-patching": ["xdump", "runtime-test"],
    "save": ["fallrimtools", "runtime-test"],
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def index_rules(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        r["rule_id"]: r
        for r in pack.get("rules", [])
        if isinstance(r, dict) and r.get("rule_id")
    }


def index_handlers(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        h["rule_id"]: h
        for h in registry.get("handlers", [])
        if isinstance(h, dict) and h.get("rule_id")
    }


def choose_rule_ids(bug: dict[str, Any], explicit: list[str]) -> list[str]:
    ids = list(explicit)
    reg = bug.get("regression") or {}
    if reg.get("analyzer_rule_id"):
        ids.append(reg["analyzer_rule_id"])
    for value in bug.get("evidence") or []:
        if isinstance(value, str) and value.startswith("SKYRIM-"):
            ids.append(value)
    out = []
    seen = set()
    for rid in ids:
        if rid and rid not in seen:
            seen.add(rid)
            out.append(rid)
    return out


def derive_mode(
    rules: list[dict[str, Any]],
    handlers_by_rule: dict[str, dict[str, Any]],
) -> tuple[str, str, bool, bool]:
    if not rules:
        return (
            "proposal",
            "No validated prevention rule is matched; repair must remain hypothesis-driven.",
            True,
            False,
        )

    modes = [MODE_MAP.get((r.get("fix_policy") or {}).get("mode"), "proposal") for r in rules]
    if "forbidden" in modes:
        return "forbidden", "At least one matched rule has no approved fix path.", False, False
    if "manual" in modes:
        return "manual", "At least one matched rule requires supervised/manual repair.", True, False
    if "proposal" in modes:
        return "proposal", "Matched rule policy requires review before mutation.", True, True

    missing = [
        r["rule_id"] for r in rules
        if not handlers_by_rule.get(r["rule_id"])
        or not handlers_by_rule[r["rule_id"]].get("automatic", False)
    ]
    if missing:
        return (
            "proposal",
            "Rule marks fix automatic, but no registered executable automatic repair handler exists for: "
            + ", ".join(missing),
            True,
            True,
        )

    unsafe = [
        r["rule_id"] for r in rules
        if not handlers_by_rule[r["rule_id"]].get("reversible", False)
        or not handlers_by_rule[r["rule_id"]].get("checkpoint_required", False)
    ]
    if unsafe:
        return (
            "proposal",
            "Registered repair handler is not both reversible and checkpointed for: "
            + ", ".join(unsafe),
            False,
            False,
        )

    has_rule_post = all((r.get("fix_policy") or {}).get("postconditions") for r in rules)
    has_handler_post = all(
        handlers_by_rule[r["rule_id"]].get("postconditions")
        for r in rules
    )
    if not has_rule_post or not has_handler_post:
        return "proposal", "Automatic repair lacks explicit rule/handler postconditions.", True, False
    return (
        "automatic",
        "All matched rules have registered reversible automatic handlers with checkpoints and explicit postconditions.",
        True,
        True,
    )


def validators_for(rules: list[dict[str, Any]], layer: str | None) -> list[str]:
    vals: list[str] = []
    scopes = []
    for rule in rules:
        scopes.extend(rule.get("scope") or [])
    if layer:
        scopes.append(layer)
    for scope in scopes:
        vals.extend(LAYER_VALIDATORS.get(scope, []))
    if not vals:
        vals = ["narrow-validator", "independent-validator"]
    out = []
    for v in vals:
        if v not in out:
            out.append(v)
    return out


def plan(
    bug: dict[str, Any],
    pack: dict[str, Any],
    *,
    explicit_rule_ids: list[str] | None = None,
    handler_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    explicit_rule_ids = explicit_rule_ids or []
    if handler_registry is None:
        handler_registry = load(DEFAULT_HANDLER_REGISTRY) if DEFAULT_HANDLER_REGISTRY.exists() else {"handlers": []}
    handlers_by_rule = index_handlers(handler_registry)
    rules_by_id = index_rules(pack)
    matched_ids = choose_rule_ids(bug, explicit_rule_ids)
    matched = [rules_by_id[rid] for rid in matched_ids if rid in rules_by_id]
    unknown_ids = [rid for rid in matched_ids if rid not in rules_by_id]

    layer = bug.get("layer") or (matched[0].get("scope", [None])[0] if matched else "unknown")
    mode, reason, reversible, provable = derive_mode(matched, handlers_by_rule)

    if unknown_ids:
        mode = "proposal"
        provable = False
        reason = f"Unknown analyzer rule ids require research before repair: {', '.join(unknown_ids)}"

    hypotheses = []
    if matched:
        for rank, rule in enumerate(matched, 1):
            detect = rule.get("detection") or {}
            hypotheses.append({
                "id": f"h{rank}",
                "cause": rule.get("title", rule["rule_id"]),
                "rank": rank,
                "confidence": "high" if bug.get("root_cause") else "medium",
                "supporting_evidence": [
                    x for x in [
                        bug.get("first_causal_error"),
                        bug.get("root_cause"),
                        f"Matched analyzer rule {rule['rule_id']}",
                    ] if x
                ],
                "contradicting_evidence": [],
                "test": {
                    "action": detect.get("algorithm") or "Run the rule detector against the failing artifact.",
                    "adapter": validators_for([rule], layer)[0],
                    "expected_if_true": f"Detector reproduces {rule['rule_id']} on the failing fixture.",
                    "expected_if_false": "Detector does not reproduce the suspected rule; demote this hypothesis and test the next one.",
                    "cost": "low",
                    "destructive": False,
                },
            })
    else:
        hypotheses.append({
            "id": "h1",
            "cause": bug.get("root_cause") or "Unknown root cause; isolate the first causal failure.",
            "rank": 1,
            "confidence": "low" if not bug.get("root_cause") else "medium",
            "supporting_evidence": [x for x in [bug.get("first_causal_error"), bug.get("root_cause")] if x],
            "contradicting_evidence": [],
            "test": {
                "action": "Reproduce the failure on the smallest isolated fixture and collect the first causal error.",
                "adapter": "minimal-fixture",
                "expected_if_true": "The same first causal failure reproduces deterministically.",
                "expected_if_false": "The failure depends on environment/integration state; bisect dependencies instead of mutating source.",
                "cost": "medium",
                "destructive": False,
            },
        })

    postconditions = []
    algorithms = []
    for rule in matched:
        fix = rule.get("fix_policy") or {}
        if fix.get("algorithm"):
            algorithms.append(fix["algorithm"])
        postconditions.extend(fix.get("postconditions") or [])

    repair_actions = []
    if algorithms and mode != "forbidden":
        action_index = 0
        for rule in matched:
            algo = (rule.get("fix_policy") or {}).get("algorithm")
            if not algo:
                continue
            action_index += 1
            handler = handlers_by_rule.get(rule["rule_id"])
            action = {
                "id": f"repair-{action_index}",
                "action": algo,
                "adapter": validators_for(matched, layer)[0],
                "mutates": True,
                "scope": [layer] if layer else ["unknown"],
                "depends_on": [] if action_index == 1 else [f"repair-{action_index-1}"],
                "safe_retry": mode == "automatic",
                "expected_outputs": [],
            }
            if handler:
                action["handler_id"] = handler["handler_id"]
            repair_actions.append(action)

    validators = validators_for(matched, layer)
    regression_tests = []
    for rule in matched:
        regression_tests.append(f"Regression fixture must reproduce and reject {rule['rule_id']}.")
    if bug.get("regression", {}).get("test_id"):
        regression_tests.append(str(bug["regression"]["test_id"]))

    issue_codes = matched_ids or [bug.get("bug_id", "UNKNOWN")]
    repair_id = f"repair-{bug.get('bug_id','unknown')}"

    return {
        "schema_version": "skyrim-repair-plan-v1",
        "repair_id": repair_id,
        "project_id": bug.get("project_id", "unknown"),
        "build_id": bug.get("build_id"),
        "bug_id": bug.get("bug_id"),
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "failure": {
            "summary": bug.get("symptom") or "Unspecified failure",
            "first_causal_error": bug.get("first_causal_error", ""),
            "issue_codes": issue_codes,
            "failing_task": bug.get("failing_task", ""),
            "adapter": bug.get("adapter", ""),
            "exit_code": bug.get("exit_code"),
            "evidence": bug.get("evidence") or [],
            "changed_files": bug.get("changed_files") or [],
            "input_hashes": {},
            "output_hashes": {},
        },
        "classification": {
            "layer": layer or "unknown",
            "failure_kind": (
                "generated-output" if "generated-output" in [s for r in matched for s in r.get("scope", [])]
                else "schema" if any((r.get("detection") or {}).get("kind") in {"plugin", "config"} for r in matched)
                else "unknown"
            ),
            "confidence": "high" if bug.get("root_cause") and matched else "medium" if matched else "low",
            "matched_rule_ids": [r["rule_id"] for r in matched],
        },
        "hypotheses": hypotheses,
        "policy": {
            "mode": mode,
            "reason": reason,
            "reversible": reversible,
            "postconditions_provable": provable,
            "requires_user_decision": mode in {"manual", "forbidden"} and layer in {"save", "navmesh", "quest-dialogue"},
            "decision_reason": "",
        },
        "repair": {
            "selected_hypothesis": "h1" if mode == "automatic" and len(hypotheses) == 1 else "",
            "actions": repair_actions,
            "downstream_invalidations": [
                "Rebuild only DAG nodes downstream of the mutated artifact.",
            ],
        },
        "validation": {
            "preconditions": [
                "Preserve original failing artifacts/logs and create a git/worktree checkpoint before mutation.",
                "Reproduce the first causal failure before applying a repair.",
            ],
            "postconditions": list(dict.fromkeys(postconditions)) or [
                "Original failure no longer reproduces.",
                "No new unexplained diff/error is introduced.",
            ],
            "independent_validators": validators,
            "runtime_assertions": [
                "Rerun the narrow runtime assertion when the affected behavior cannot be proven statically."
            ] if layer in {"native", "runtime-patching", "save", "behavior", "animation", "world", "navmesh"} else [],
            "regression_tests": list(dict.fromkeys(regression_tests)),
            "mutation_test": "Add or preserve a deliberately broken fixture proving the detector rejects this bug class.",
        },
        "rollback": {
            "strategy": "Restore the pre-repair git/worktree checkpoint and discard only generated downstream outputs from the failed attempt.",
            "checkpoint_required": True,
            "checkpoint": "",
            "bad_fix_rollback_automatic": True,
        },
        "result": {
            "status": "planned",
            "attempts": 0,
            "evidence": [],
            "new_issue_codes": [],
            "regression_promoted": False,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bug", type=Path)
    ap.add_argument("--rule-pack", type=Path, required=True)
    ap.add_argument("--handler-registry", type=Path, default=DEFAULT_HANDLER_REGISTRY)
    ap.add_argument("--rule-id", action="append", default=[])
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    result = plan(
        load(args.bug),
        load(args.rule_pack),
        explicit_rule_ids=args.rule_id,
        handler_registry=load(args.handler_registry),
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
