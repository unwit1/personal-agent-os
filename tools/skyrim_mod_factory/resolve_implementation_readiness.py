#!/usr/bin/env python3
"""Classify Skyrim Mod Factory questions by who/what should resolve them.

Low-level implementation questions should go to project context, schemas, source
research, static analysis, or runtime tests before they ever reach the user.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path | None) -> dict[str, Any]:
    return {} if path is None else json.loads(path.read_text(encoding="utf-8"))


def qid(topic: str, name: str) -> str:
    raw = f"{topic}.{name}".lower()
    return "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in raw).strip("-")


def add_question(
    out: list[dict[str, Any]],
    *,
    topic: str,
    name: str,
    question: str,
    disposition: str,
    blocker: bool,
    confidence: str = "unknown",
    answer: Any = None,
    source: str = "unknown",
    evidence: list[str] | None = None,
    next_action: str = "",
    adapters: list[str] | None = None,
    safe_default: bool = False,
    reversible: bool = True,
    notes: str = "",
) -> None:
    ident = qid(topic, name)
    if any(item["question_id"] == ident for item in out):
        return
    item: dict[str, Any] = {
        "question_id": ident,
        "topic": topic,
        "question": question,
        "disposition": disposition,
        "blocker": blocker,
        "answer": answer,
        "confidence": confidence,
        "resolution_source": source,
        "evidence": evidence or [],
        "next_action": next_action,
        "adapters": adapters or [],
        "safe_default": safe_default,
        "reversible": reversible,
    }
    if notes:
        item["notes"] = notes
    out.append(item)


def exact_runtime_from_lock(lock: dict[str, Any]) -> str | None:
    for key in ("game_runtime", "runtime", "skyrim_runtime"):
        val = lock.get(key)
        if isinstance(val, str) and val:
            return val
    game = lock.get("game")
    if isinstance(game, dict):
        for key in ("runtime", "version", "executable_version"):
            val = game.get(key)
            if isinstance(val, str) and val:
                return val
    return None


def classify_freeform(question: str) -> tuple[str, str, list[str], str]:
    s = question.lower()
    if any(x in s for x in ("license", "redistribution", "public release rights")):
        return (
            "user-required",
            "licensing",
            [],
            "Apply an existing project license policy if one exists; otherwise ask for the release/redistribution decision.",
        )
    if any(x in s for x in ("aesthetic", "visual style", "balance", "feel", "player-facing choice")):
        return (
            "user-required",
            "creative-intent",
            [],
            "Ask only for the creative/product choice that cannot be derived from project canon or requirements.",
        )
    if any(x in s for x in ("exact executable", "runtime", "steam", "gog", "vr")):
        return (
            "research-required",
            "runtime",
            ["doctor-toolchain", "xdump"],
            "Inspect the project/toolchain lock and local runtime before asking the user.",
        )
    if any(x in s for x in ("schema version", "upgrade", "uninstall", "existing save", "migration")):
        return (
            "research-required",
            "persistence",
            ["fallrimtools", "devbench"],
            "Inspect release history and persisted-state schemas, then generate migration fixtures.",
        )
    if any(x in s for x in ("which tool", "framework", "implementation", "architecture", "record field", "formid", "editorid", "api")):
        return (
            "research-required",
            "architecture",
            ["mutagen", "xdump"],
            "Resolve from implementation patterns, provider registry, and pinned source/schema evidence.",
        )
    if any(x in s for x in ("works", "behavior", "in game", "save/load", "crash")):
        return (
            "test-required",
            "testing",
            ["devbench"],
            "Build the smallest discriminating runtime fixture and assert the result.",
        )
    return (
        "research-required",
        "unknown",
        [],
        "Search project context, knowledge corpus, upstream source, and analogous vanilla data before escalating.",
    )


def derive(
    manifest: dict[str, Any],
    *,
    quality: dict[str, Any] | None = None,
    feature: dict[str, Any] | None = None,
    toolchain: dict[str, Any] | None = None,
) -> dict[str, Any]:
    quality = quality or {}
    feature = feature or {}
    toolchain = toolchain or {}
    questions: list[dict[str, Any]] = []

    project_id = manifest.get("project_id")
    layers = set(manifest.get("layers") or [])
    targets = list(manifest.get("targets") or [])
    persistence = manifest.get("persistence") or {}
    release = manifest.get("release") or {}
    plugin_policy = manifest.get("plugin_policy") or {}
    frameworks = manifest.get("frameworks") or []
    outputs = manifest.get("outputs") or []
    exact_runtime = exact_runtime_from_lock(toolchain)

    if "other" in targets:
        if exact_runtime:
            add_question(
                questions,
                topic="runtime",
                name="target-other",
                question="What exact runtime does target 'other' represent?",
                disposition="auto-resolved",
                blocker=False,
                confidence="high",
                answer=exact_runtime,
                source="toolchain",
                evidence=["Exact runtime found in toolchain lock."],
                adapters=["doctor-toolchain"],
            )
        else:
            add_question(
                questions,
                topic="runtime",
                name="target-other",
                question="What exact runtime does target 'other' represent?",
                disposition="research-required",
                blocker=True,
                next_action="Probe the installed Skyrim executable/distribution and write it into the toolchain lock.",
                adapters=["doctor-toolchain"],
            )

    if "native" in layers and any(t in {"ae-steam", "ae-gog", "ae-1.7.x"} for t in targets):
        if exact_runtime:
            add_question(
                questions,
                topic="runtime",
                name="native-exact-runtime",
                question="What exact executable version must the native DLL support?",
                disposition="auto-resolved",
                blocker=False,
                confidence="high",
                answer=exact_runtime,
                source="toolchain",
                evidence=["Exact executable version supplied by toolchain lock."],
                adapters=["doctor-toolchain"],
            )
        else:
            add_question(
                questions,
                topic="runtime",
                name="native-exact-runtime",
                question="What exact executable version must the native DLL support?",
                disposition="research-required",
                blocker=True,
                next_action="Read local executable version, SKSE, Address Library, and CommonLib lock.",
                adapters=["doctor-toolchain"],
            )

    if "records" in layers and not plugin_policy.get("kind"):
        add_question(
            questions,
            topic="architecture",
            name="plugin-kind",
            question="Which plugin kind should this project use?",
            disposition="research-required",
            blocker=True,
            next_action="Count new forms, masters, persistence constraints, and runtime targets; select the least invasive safe plugin kind.",
            adapters=["mutagen", "xdump"],
            notes="Do not default to ESP-FE until form identity/compaction safety is proven.",
        )

    for fw in frameworks:
        if not isinstance(fw, dict):
            continue
        fid = str(fw.get("id") or "").strip()
        if fid and not fw.get("version"):
            add_question(
                questions,
                topic="framework",
                name=f"version-{fid}",
                question=f"What exact version of framework '{fid}' should be pinned?",
                disposition="research-required",
                blocker=bool(fw.get("required", True)),
                next_action="Inspect current upstream release/source compatibility and pin the version/source ref.",
                adapters=["tool-registry"],
            )

    for idx, output in enumerate(outputs):
        if not isinstance(output, dict) or not output.get("generated", True):
            continue
        if output.get("type") in {"report", "other"}:
            continue
        if not output.get("generator"):
            add_question(
                questions,
                topic="architecture",
                name=f"generator-{idx}-{output.get('type', 'unknown')}",
                question=f"Which generator should create '{output.get('path', '?')}' ({output.get('type', 'unknown')})?",
                disposition="research-required",
                blocker=True,
                next_action="Resolve the output type through the capability registry and choose an independently verifiable generator.",
                adapters=["tool-registry"],
            )

    uses_persistence = any(
        bool(persistence.get(k))
        for k in ("uses_save_state", "uses_skse_cosave", "uses_external_state")
    )
    if uses_persistence and persistence.get("schema_version") is None:
        add_question(
            questions,
            topic="persistence",
            name="schema-version",
            question="What persisted-state schema version should this release use?",
            disposition="research-required",
            blocker=True,
            next_action="Inspect release history. If there is no prior persisted release, assign version 1; otherwise derive the migration version.",
            adapters=["git-history", "fallrimtools"],
        )

    if uses_persistence and persistence.get("supports_upgrade") is None:
        add_question(
            questions,
            topic="persistence",
            name="upgrade-policy",
            question="Must this release support upgrading existing saves from a prior released version?",
            disposition="research-required",
            blocker=True,
            next_action="Inspect release history and support policy; ask only if support vs breakage remains a product decision.",
            adapters=["git-history", "fallrimtools", "devbench"],
            reversible=False,
        )

    if uses_persistence and persistence.get("supports_uninstall") is None:
        add_question(
            questions,
            topic="persistence",
            name="uninstall-policy",
            question="Can this mod safely support mid-save uninstall?",
            disposition="test-required",
            blocker=False,
            next_action="Derive every persisted store/reference and run uninstall fixtures. Document 'not proven safe' until evidence exists.",
            adapters=["fallrimtools", "devbench"],
            answer="not proven safe",
            source="default-policy",
            confidence="medium",
            safe_default=True,
        )

    if not release.get("license"):
        add_question(
            questions,
            topic="licensing",
            name="release-license",
            question="What license/redistribution policy applies to the release and bundled/generated assets?",
            disposition="user-required",
            blocker=True,
            next_action="First inspect repository/project policy and dependency licenses; ask only if no durable policy exists.",
            adapters=["dependency-license-audit"],
            reversible=False,
        )

    impl = feature.get("implementation") or {}
    for i, question in enumerate(impl.get("open_architecture_questions") or []):
        disp, topic, adapters, action = classify_freeform(str(question))
        add_question(
            questions,
            topic=topic,
            name=f"feature-open-{i}",
            question=str(question),
            disposition=disp,
            blocker=True,
            next_action=action,
            adapters=adapters,
        )

    for i, question in enumerate(quality.get("blocking_questions") or []):
        disp, topic, adapters, action = classify_freeform(str(question))
        add_question(
            questions,
            topic=topic,
            name=f"quality-open-{i}",
            question=str(question),
            disposition=disp,
            blocker=True,
            next_action=action,
            adapters=adapters,
            reversible=topic not in {"licensing", "persistence"},
        )

    for ac in feature.get("acceptance_criteria") or []:
        if not isinstance(ac, dict):
            continue
        if ac.get("automatable") is False and ac.get("kind") in {"visual", "performance", "runtime"}:
            add_question(
                questions,
                topic="testing",
                name=f"supervised-{ac.get('id', 'criterion')}",
                question=f"How will acceptance criterion '{ac.get('id', 'criterion')}' be verified?",
                disposition="test-required",
                blocker=True,
                next_action="Generate a supervised runtime/visual fixture; request subjective approval only after deterministic checks pass.",
                adapters=["devbench"],
            )

    counts = {
        "total": len(questions),
        "auto_resolved": sum(q["disposition"] == "auto-resolved" for q in questions),
        "research_required": sum(q["disposition"] == "research-required" for q in questions),
        "test_required": sum(q["disposition"] == "test-required" for q in questions),
        "user_required": sum(q["disposition"] == "user-required" for q in questions),
        "blocked": sum(q["disposition"] == "blocked" for q in questions),
    }

    if counts["blocked"]:
        status = "blocked"
    elif any(q["blocker"] and q["disposition"] == "user-required" for q in questions):
        status = "user-decision-required"
    elif any(q["blocker"] and q["disposition"] == "test-required" for q in questions):
        status = "test-required"
    elif any(q["blocker"] and q["disposition"] == "research-required" for q in questions):
        status = "research-required"
    else:
        status = "ready"

    return {
        "schema_version": "skyrim-implementation-readiness-v1",
        "project_id": project_id,
        "feature_id": feature.get("feature_id"),
        "status": status,
        "summary": counts,
        "questions": questions,
        "decisions": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--quality-plan", type=Path)
    ap.add_argument("--feature-intent", type=Path)
    ap.add_argument("--toolchain-lock", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    result = derive(
        load_json(args.manifest),
        quality=load_json(args.quality_plan),
        feature=load_json(args.feature_intent),
        toolchain=load_json(args.toolchain_lock),
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
