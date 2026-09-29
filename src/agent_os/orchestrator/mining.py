"""Failure and success mining: ``agent-os orchestrate mining`` (MIE-0004).

Aggregates the typed FAIL and SUC evidence records into stable signature
clusters and reports recurrence, status and coverage, deterministically and
with no model call. It turns the record store into a small dashboard the
improvement loop can act on:

* **failure clusters** by ``signature``: total recurrence, how many are still
  open, the task families touched, and whether an open cluster links to a
  regression test or an experiment (an open, recurring failure with neither is
  flagged -- the constitution asks every recurring failure to reach a
  regression case and an experiment);
* **success patterns** (SUC) by signature, with a reuse hint;
* **the top recurring signatures**, so the highest-impact failures surface.

Reads records under ``projects/personal-agent-os/orchestrator-os/records/``;
writes nothing unless ``--write`` stores the report.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from ..paths import ROOT

RECORDS = ROOT / "projects" / "personal-agent-os" / "orchestrator-os" / "records"
REPORT = ROOT / "projects" / "personal-agent-os" / "orchestrator-os" / "mining-report.json"
OPEN_STATES = {"open", "active", "proposed"}
# A link whose rel/ref shows the failure reached a test or an experiment.
COVERAGE_RELS = {"tests", "regression", "measured_by"}


def _load(kind_dir: str, records: Path | None = None) -> list[dict[str, Any]]:
    root = Path(records or RECORDS) / kind_dir
    out = []
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("id"):
            out.append(data)
    return out


def _covered(record: dict[str, Any]) -> bool:
    """A failure is 'covered' when it links to a regression test or an
    experiment, or names a regression case, or an EXP references it."""
    for link in record.get("links") or []:
        rel, ref = str(link.get("rel")), str(link.get("ref"))
        if rel in COVERAGE_RELS:
            return True
        if ref.startswith(("EXP-", "tests/")) or ref.endswith("_test.py") or "test_" in ref:
            return True
    return bool(record.get("regression_case"))


def cluster_failures(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[str(record.get("signature") or record["id"])].append(record)
    clusters = []
    for signature, members in groups.items():
        open_members = [m for m in members if m.get("status") in OPEN_STATES]
        families = sorted({str(m.get("task_family")) for m in members if m.get("task_family")})
        recurrence = sum(int(m.get("recurrence") or 1) for m in members)
        covered = all(_covered(m) for m in members)
        clusters.append({
            "signature": signature,
            "records": sorted(m["id"] for m in members),
            "occurrences": recurrence,
            "distinct_records": len(members),
            "open": len(open_members),
            "task_families": families,
            "covered": covered,
            "needs_coverage": bool(open_members) and recurrence >= 2 and not covered,
        })
    clusters.sort(key=lambda item: (-item["occurrences"], item["signature"]))
    return clusters


def cluster_successes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[str(record.get("signature") or record["id"])].append(record)
    out = [{"signature": signature, "records": sorted(m["id"] for m in members),
            "occurrences": sum(int(m.get("recurrence") or 1) for m in members),
            "reusable_hint": any("skill" in str(m.get("summary", "")).lower() or "reusable" in str(m.get("summary", "")).lower() for m in members)}
           for signature, members in groups.items()]
    out.sort(key=lambda item: (-item["occurrences"], item["signature"]))
    return out


def build(records: Path | None = None) -> dict[str, Any]:
    failures = _load("failures", records)
    successes = _load("successes", records)
    fail_clusters = cluster_failures(failures)
    return {
        "schema": "personal-agent/mining-report/v1",
        "generated_at": date.today().isoformat(),
        "totals": {
            "failure_records": len(failures),
            "failure_signatures": len(fail_clusters),
            "open_failures": sum(1 for f in failures if f.get("status") in OPEN_STATES),
            "signatures_needing_coverage": sum(1 for c in fail_clusters if c["needs_coverage"]),
            "success_records": len(successes),
        },
        "needs_coverage": [c for c in fail_clusters if c["needs_coverage"]],
        "top_failure_signatures": fail_clusters[:10],
        "failure_clusters": fail_clusters,
        "success_patterns": cluster_successes(successes),
        "notes": ["A signature 'needs coverage' when it is open, has recurred (>=2), and links to no regression test or experiment.",
                  "Recurrence sums each record's recurrence field; supersede records rather than editing them (negative evidence is append-only)."],
    }


def write(report: dict[str, Any], path: Path | None = None) -> str:
    target = Path(path or REPORT)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target)
