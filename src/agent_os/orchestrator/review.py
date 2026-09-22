"""Structured cross-review findings.

A review is only usable when it parses into a verdict plus findings with
severity, path, summary, evidence, recommended action and disposition. Free
text such as "looks good" is a malformed result, not an approval.
"""

from __future__ import annotations

from typing import Any

from .model import DISPOSITIONS, SEVERITIES
from .store import redact


VERDICTS = ("approved", "changes_requested", "blocked")
MAX_FINDINGS = 25


class MalformedReview(ValueError):
    pass


def parse_review(structured: dict[str, Any] | None, round_number: int, reviewer: str) -> dict[str, Any]:
    if not isinstance(structured, dict):
        raise MalformedReview("review produced no structured result block")
    verdict = str(structured.get("verdict") or "").strip().lower()
    if verdict not in VERDICTS:
        raise MalformedReview(f"review verdict must be one of {VERDICTS}")
    raw_findings = structured.get("findings")
    if not isinstance(raw_findings, list):
        raise MalformedReview("review findings must be a list (empty when there are none)")
    findings = []
    for index, raw in enumerate(raw_findings[:MAX_FINDINGS], start=1):
        if not isinstance(raw, dict):
            raise MalformedReview(f"finding {index} is not an object")
        severity = str(raw.get("severity") or "").strip().lower()
        if severity not in SEVERITIES:
            raise MalformedReview(f"finding {index} has unsupported severity {severity!r}")
        summary = str(raw.get("summary") or "").strip()
        if not summary:
            raise MalformedReview(f"finding {index} has no summary")
        findings.append(
            {
                "id": f"R{round_number}-{str(raw.get('id') or index)[:24]}",
                "round": round_number,
                "reviewer": reviewer,
                "severity": severity,
                "path": redact(raw.get("path") or raw.get("file") or "", 300) or None,
                "summary": redact(summary, 300),
                "evidence": redact(raw.get("evidence") or "", 500) or None,
                "recommended_action": redact(raw.get("recommended_action") or "", 300) or None,
                "disposition": "open",
                "disposition_reason": None,
                "validator_needed": bool(raw.get("validator_needed", severity in {"critical", "high"})),
            }
        )
    if verdict == "approved" and any(item["severity"] in {"critical", "high"} for item in findings):
        # A self-contradictory review is not trusted either way.
        verdict = "changes_requested"
    return {"verdict": verdict, "findings": findings, "summary": redact(structured.get("summary") or "", 400) or None}


def material(findings: list[dict[str, Any]], severities: list[str]) -> list[dict[str, Any]]:
    return [item for item in findings if item["severity"] in severities and item["disposition"] in {"open", "accepted"}]


def apply_dispositions(findings: list[dict[str, Any]], structured: dict[str, Any] | None) -> None:
    """Record a repairer's per-finding dispositions (fixed / rejected with reason)."""
    reported = (structured or {}).get("dispositions")
    if not isinstance(reported, list):
        return
    by_id = {item["id"]: item for item in findings}
    for entry in reported:
        if not isinstance(entry, dict):
            continue
        finding = by_id.get(str(entry.get("id")))
        disposition = str(entry.get("disposition") or "").lower()
        if finding is None or disposition not in DISPOSITIONS:
            continue
        if disposition == "rejected" and not str(entry.get("reason") or "").strip():
            continue  # rejection needs a reason
        finding["disposition"] = disposition
        finding["disposition_reason"] = redact(entry.get("reason") or "", 300) or None
