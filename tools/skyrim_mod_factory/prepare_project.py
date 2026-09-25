#!/usr/bin/env python3
"""Prepare a Skyrim Mod Factory project in one deterministic pass.

Pipeline:
source manifest + optional typed feature intent
-> conservative implementation-pattern selection
-> effective planning manifest (source manifest remains untouched)
-> quality plan + provider resolution
-> optional toolchain doctor
-> build DAG + implementation-readiness queue + test matrix
-> preparation report.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


QUALITY = load_module("quality", "derive_quality_plan.py")
DAG = load_module("dag", "compile_build_dag.py")
DOCTOR = load_module("doctor", "doctor_toolchain.py")
READINESS = load_module("readiness", "resolve_implementation_readiness.py")
TEST_MATRIX = load_module("test_matrix", "derive_test_matrix.py")
SELECTOR = load_module("selector", "select_implementation_pattern.py")
RUNTIME_SMOKE = load_module("runtime_smoke", "derive_runtime_smoke.py")
RUNTIME_CONTEXT = load_module(
    "runtime_context", "build_runtime_execution_context.py"
)


def uniq(xs):
    out = []
    seen = set()
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_pattern_pack(path: Path) -> dict[str, Any]:
    return load_json(path) if path.exists() else {"patterns": []}


def load_patterns(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        p["pattern_id"]: p
        for p in pack.get("patterns", [])
        if isinstance(p, dict) and p.get("pattern_id")
    }


def load_providers(path: Path):
    if not path.exists():
        return {}
    data = load_json(path)
    return {p["provider_id"]: p for p in data.get("providers", [])}


def load_adapter_ids(path: Path):
    if not path.exists():
        return set()
    data = load_json(path)
    return {p["adapter_id"] for p in data.get("adapters", [])}


def resolve_provider(token, providers, adapter_ids, seen=None):
    """Return (kind, resolved adapter or None, provider record or None)."""
    if token in adapter_ids:
        return "adapter", token, None
    seen = set(seen or ())
    if token in seen:
        return "unknown", None, None
    seen.add(token)
    p = providers.get(token)
    if not p:
        return "unknown", None, None
    kind = p.get("kind")
    if kind == "alias":
        if p.get("adapter_id"):
            aid = p["adapter_id"]
            return ("adapter", aid, p) if aid in adapter_ids else ("unknown", None, p)
        if p.get("resolves_to"):
            k, a, _ = resolve_provider(p["resolves_to"], providers, adapter_ids, seen)
            return k, a, p
    return kind, p.get("adapter_id"), p


def enrich_quality(manifest, quality, patterns, providers=None, adapter_ids=None):
    providers = providers or {}
    adapter_ids = set(adapter_ids or ())
    selected = []
    pattern_issues = []
    provider_issues = []
    implementation_providers = []
    frameworks = []
    strategies = []
    references = []
    unadapted_preferred = []
    reasons = quality.setdefault("reasons", {})
    quality.setdefault("adapters", {}).setdefault("preferred", [])
    quality["adapters"].setdefault("supporting", [])
    features = manifest.get("features") or []

    def apply_provider(token, preference):
        kind, adapter, meta = resolve_provider(token, providers, adapter_ids)
        row = {"provider_id": token, "kind": kind, "preference": preference}
        if adapter:
            row["resolved_adapter"] = adapter
        implementation_providers.append(row)
        validations = (meta or {}).get("validation_adapters", [])
        if preference == "preferred":
            if kind == "adapter" and adapter:
                quality["adapters"]["preferred"] = uniq(quality["adapters"]["preferred"] + [adapter])
            elif kind == "framework":
                frameworks.append(token)
            elif kind == "strategy":
                strategies.append(token)
            elif kind == "reference":
                references.append(token)
            elif kind == "unadapted-tool":
                unadapted_preferred.append(token)
            elif kind == "pattern":
                strategies.append(f"pattern:{(meta or {}).get('pattern_id', token)}")
            else:
                provider_issues.append(f"preferred:{token}:unclassified provider")
        else:
            if kind == "adapter" and adapter and adapter not in quality["adapters"]["preferred"]:
                quality["adapters"]["supporting"] = uniq(quality["adapters"]["supporting"] + [adapter])
            elif kind == "unknown":
                provider_issues.append(f"alternative:{token}:unclassified provider")
        for aid in validations:
            if aid in adapter_ids and aid not in quality["adapters"]["preferred"]:
                quality["adapters"]["supporting"] = uniq(quality["adapters"]["supporting"] + [aid])

    for feature in features:
        pid = feature.get("pattern_id")
        if not pid:
            continue
        pat = patterns.get(pid)
        if not pat:
            pattern_issues.append(
                f"Unknown implementation pattern '{pid}' for feature '{feature.get('feature_id')}'."
            )
            continue
        selected.append(pid)
        val = pat.get("validation") or {}
        for gate in val.get("gates", []):
            if gate not in quality["gates"]:
                quality["gates"].append(gate)
            reasons.setdefault(gate, [])
            marker = f"pattern:{pid}"
            if marker not in reasons[gate]:
                reasons[gate].append(marker)
        quality["runtime_scenarios"] = uniq(
            quality.get("runtime_scenarios", []) + val.get("runtime_tests", [])
        )
        quality["mutation_tests"] = uniq(
            quality.get("mutation_tests", []) + val.get("negative_tests", [])
        )
        quality["human_checks"] = uniq(
            quality.get("human_checks", []) + val.get("human_checks", [])
        )
        sel = pat.get("selection") or {}
        for token in sel.get("preferred", []):
            apply_provider(token, "preferred")
        for token in sel.get("alternatives", []):
            apply_provider(token, "alternative")

    quality["gates"] = sorted(set(quality["gates"]), key=lambda x: int(x[1:]))
    quality["adapters"]["preferred"] = uniq(quality["adapters"]["preferred"])
    quality["adapters"]["supporting"] = uniq(
        x
        for x in quality["adapters"]["supporting"]
        if x not in quality["adapters"]["preferred"]
    )
    quality["selected_patterns"] = uniq(selected)
    quality["pattern_issues"] = uniq(pattern_issues)
    quality["implementation_providers"] = implementation_providers
    quality["framework_dependencies"] = uniq(frameworks)
    quality["strategy_dependencies"] = uniq(strategies)
    quality["reference_dependencies"] = uniq(references)
    quality["unadapted_providers"] = uniq(unadapted_preferred)
    quality["provider_issues"] = uniq(provider_issues)
    return quality


def make_effective_manifest(
    manifest: dict[str, Any],
    feature: dict[str, Any],
    selection: dict[str, Any] | None,
    patterns: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Apply validated planning deductions without mutating the source manifest."""
    effective = copy.deepcopy(manifest)
    deductions = []
    if not feature:
        return effective, deductions

    fid = feature.get("feature_id")
    selected_pattern = (selection or {}).get("selected_pattern")
    impl = feature.get("implementation") or {}

    required_layers = list(impl.get("selected_layers") or [])
    if selected_pattern and selected_pattern in patterns:
        required_layers += patterns[selected_pattern].get("preferred_layers", [])
        deductions.append(f"planning pattern selected: {selected_pattern}")

    if required_layers:
        before = list(effective.get("layers") or [])
        effective["layers"] = uniq(before + required_layers)
        added = [x for x in effective["layers"] if x not in before]
        if added:
            deductions.append("planning layers added: " + ", ".join(added))

    features = effective.setdefault("features", [])
    target = next((x for x in features if x.get("feature_id") == fid), None)
    if target is None and fid:
        target = {"feature_id": fid, "intent": feature.get("summary", "")}
        features.append(target)
        deductions.append(f"planning feature added: {fid}")
    if target is not None and selected_pattern and not target.get("pattern_id"):
        target["pattern_id"] = selected_pattern
        deductions.append(f"planning feature {fid} assigned pattern: {selected_pattern}")

    return effective, deductions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="Directory that will receive generated planning/preflight artifacts",
    )
    ap.add_argument(
        "--patterns",
        type=Path,
        default=REPO / "knowledge/libraries/skyrim-modding/automation/implementation-patterns-core.json",
    )
    ap.add_argument(
        "--providers",
        type=Path,
        default=REPO / "knowledge/libraries/skyrim-modding/automation/implementation-provider-registry.json",
    )
    ap.add_argument(
        "--capabilities",
        type=Path,
        default=REPO / "knowledge/libraries/skyrim-modding/automation/tool-capability-registry.json",
    )
    ap.add_argument("--toolchain-lock", type=Path)
    ap.add_argument(
        "--runtime-worker-config",
        type=Path,
        help="Optional skyrim-runtime-worker-config-v1 used to generate executable runtime context.",
    )
    ap.add_argument(
        "--runtime-regression-test",
        type=Path,
        help="Optional typed feature/regression runtime test bound to runtime.regression.",
    )
    ap.add_argument(
        "--runtime-context-base",
        type=Path,
        help="Optional base skyrim-execution-context-v1 merged with generated runtime wiring.",
    )
    ap.add_argument(
        "--runtime-run-root",
        type=Path,
        help="Runtime result root. Defaults to <workspace>/runtime-runs.",
    )
    ap.add_argument(
        "--feature-intent",
        type=Path,
        help="Optional skyrim-feature-intent-v1 document used for pattern selection/readiness/tests.",
    )
    ap.add_argument("--no-file-check", action="store_true")
    args = ap.parse_args()

    manifest = load_json(args.manifest)
    if manifest.get("schema_version") != "skyrim-mod-project-v1":
        raise SystemExit("Expected skyrim-mod-project-v1 manifest")

    args.workspace.mkdir(parents=True, exist_ok=True)
    pattern_pack = load_pattern_pack(args.patterns)
    patterns = load_patterns(pattern_pack)
    providers = load_providers(args.providers)
    adapter_ids = load_adapter_ids(args.capabilities)
    feature = load_json(args.feature_intent)

    pattern_selection = None
    if feature:
        pattern_selection = SELECTOR.rank(feature, pattern_pack)

    effective_manifest, planning_deductions = make_effective_manifest(
        manifest, feature, pattern_selection, patterns
    )

    quality = QUALITY.derive(effective_manifest)
    quality = enrich_quality(effective_manifest, quality, patterns, providers, adapter_ids)
    dag = DAG.compile_dag(effective_manifest, quality)

    lock = load_json(args.toolchain_lock)
    doctor = None
    if args.toolchain_lock:
        doctor = DOCTOR.audit(lock, quality, effective_manifest, not args.no_file_check)

    readiness = READINESS.derive(
        effective_manifest, quality=quality, feature=feature, toolchain=lock
    )
    test_matrix = TEST_MATRIX.derive(effective_manifest, feature)
    runtime_smoke = RUNTIME_SMOKE.derive(effective_manifest)

    runtime_regression = None
    if args.runtime_regression_test:
        runtime_regression = load_json(args.runtime_regression_test)
        RUNTIME_CONTEXT.validate(
            runtime_regression,
            RUNTIME_CONTEXT.RUNTIME_TEST_SCHEMA,
            f"runtime regression test {args.runtime_regression_test}",
        )
        if runtime_regression.get("project_id") != effective_manifest.get("project_id"):
            raise SystemExit(
                "Runtime regression test project_id does not match effective manifest"
            )

    epath = args.workspace / "effective-manifest.json"
    ppath = args.workspace / "pattern-selection.json"
    qpath = args.workspace / "quality-plan.json"
    dpath = args.workspace / "build-dag.json"
    ipath = args.workspace / "implementation-readiness.json"
    tpath = args.workspace / "test-matrix.json"
    spath = args.workspace / "runtime-smoke.json"
    cpath = args.workspace / "execution-context.json"
    rpath = args.workspace / "preparation-report.json"

    epath.write_text(json.dumps(effective_manifest, indent=2) + "\n", encoding="utf-8")
    if pattern_selection is not None:
        ppath.write_text(json.dumps(pattern_selection, indent=2) + "\n", encoding="utf-8")
    qpath.write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    dpath.write_text(json.dumps(dag, indent=2) + "\n", encoding="utf-8")
    ipath.write_text(json.dumps(readiness, indent=2) + "\n", encoding="utf-8")
    tpath.write_text(json.dumps(test_matrix, indent=2) + "\n", encoding="utf-8")
    spath.write_text(json.dumps(runtime_smoke, indent=2) + "\n", encoding="utf-8")

    runtime_nodes = [
        n for n in dag.get("nodes", [])
        if n.get("phase") == "runtime" and n.get("gates")
    ]
    required_runtime_ids = [n["id"] for n in runtime_nodes]
    runtime_bindings = {}
    if "runtime.smoke" in required_runtime_ids:
        runtime_bindings["runtime.smoke"] = spath
    if "runtime.regression" in required_runtime_ids and args.runtime_regression_test:
        runtime_bindings["runtime.regression"] = args.runtime_regression_test
    unbound_runtime_ids = [
        node_id for node_id in required_runtime_ids
        if node_id not in runtime_bindings
    ]

    runtime_context = None
    if args.runtime_worker_config:
        runtime_context = RUNTIME_CONTEXT.build_context(
            project_id=effective_manifest.get("project_id"),
            dag=dag,
            worker_config_path=args.runtime_worker_config,
            run_root=args.runtime_run_root or (args.workspace / "runtime-runs"),
            smoke_test=runtime_bindings.get("runtime.smoke"),
            regression_test=runtime_bindings.get("runtime.regression"),
            base_context=load_json(args.runtime_context_base),
        )
        cpath.write_text(
            json.dumps(runtime_context, indent=2) + "\n",
            encoding="utf-8",
        )

    runtime_execution_ready = (
        not required_runtime_ids
        or (
            args.runtime_worker_config is not None
            and not unbound_runtime_ids
            and runtime_context is not None
        )
    )

    blocking_provider_issues = [
        x for x in quality.get("provider_issues", []) if x.startswith("preferred:")
    ]
    environment_ok = doctor is None or doctor.get("status") != "fail"
    pattern_resolution_ok = (
        pattern_selection is None or pattern_selection.get("status") == "selected"
    )
    readiness_ready = readiness.get("status") == "ready"
    design_ok = (
        pattern_resolution_ok
        and readiness_ready
        and not quality.get("pattern_issues")
        and not blocking_provider_issues
    )
    supervised_ready = design_ok and environment_ok and runtime_execution_ready
    autonomous_ready = supervised_ready and not quality.get("unadapted_providers")
    autonomous_resolution_ready = (
        environment_ok
        and readiness.get("summary", {}).get("user_required", 0) == 0
        and readiness.get("summary", {}).get("blocked", 0) == 0
    )

    report = {
        "schema_version": "skyrim-project-preparation-report-v1",
        "project_id": effective_manifest.get("project_id"),
        "risk_tier": quality["risk_tier"],
        "pattern_selection": pattern_selection,
        "planning_deductions": planning_deductions,
        "selected_patterns": quality.get("selected_patterns", []),
        "framework_dependencies": quality.get("framework_dependencies", []),
        "unadapted_preferred_providers": quality.get("unadapted_providers", []),
        "pattern_issues": quality.get("pattern_issues", []),
        "provider_issues": quality.get("provider_issues", []),
        "legacy_blocking_questions": quality.get("blocking_questions", []),
        "implementation_readiness": readiness.get("status"),
        "readiness_summary": readiness.get("summary", {}),
        "user_required_questions": [
            q for q in readiness.get("questions", []) if q.get("disposition") == "user-required"
        ],
        "research_queue": [
            q for q in readiness.get("questions", []) if q.get("disposition") == "research-required"
        ],
        "test_queue": [
            q for q in readiness.get("questions", []) if q.get("disposition") == "test-required"
        ],
        "pattern_research_required": (
            pattern_selection is not None
            and pattern_selection.get("status") != "selected"
        ),
        "gate_count": len(quality["gates"]),
        "test_case_count": len(test_matrix.get("cases", [])),
        "test_coverage_gaps": test_matrix.get("coverage", {}).get("gaps", []),
        "dag_nodes": len(dag["nodes"]),
        "toolchain": doctor,
        "runtime_execution": {
            "required_nodes": required_runtime_ids,
            "bound_nodes": sorted(runtime_bindings),
            "unbound_nodes": unbound_runtime_ids,
            "worker_config": (
                str(args.runtime_worker_config)
                if args.runtime_worker_config else None
            ),
            "execution_context": (
                str(cpath) if runtime_context is not None else None
            ),
            "ready": runtime_execution_ready,
        },
        "ready_for_execution": supervised_ready,
        "ready_for_autonomous_execution": autonomous_ready,
        "ready_for_autonomous_resolution": autonomous_resolution_ready,
        "requires_supervised_provider": supervised_ready and not autonomous_ready,
        "artifacts": {
            "effective_manifest": str(epath),
            "pattern_selection": str(ppath) if pattern_selection is not None else None,
            "quality_plan": str(qpath),
            "build_dag": str(dpath),
            "implementation_readiness": str(ipath),
            "test_matrix": str(tpath),
            "runtime_smoke": str(spath),
            "runtime_regression": (
                str(args.runtime_regression_test)
                if args.runtime_regression_test else None
            ),
            "execution_context": (
                str(cpath) if runtime_context is not None else None
            ),
        },
    }
    rpath.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

    if doctor and doctor.get("status") == "fail":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
