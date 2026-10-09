"""Ingestion queue status in the Executive window: one item per tab (Work, Personal).

Reads the local intake queues only (counts, no message content). Shows what is
waiting for the Ingester Engine, what the spam rules could not decide (model
review), and work items waiting to be distilled into PII-free RTEC-HR knowledge.
"""

from __future__ import annotations

from typing import Any, Callable


def intake_items(load_status: Callable[[], dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if load_status is None:
        from agent_os.intake import status as load_status
    try:
        status = load_status()
    except Exception:  # noqa: BLE001 -- a missing queue never breaks the window
        return []
    items = []
    for tab, stats in status.items():
        d = stats.get("deliveries") or {}
        engine, classify, promote = d.get("engine", {}), d.get("classify", {}), d.get("promote", {})
        waiting = engine.get("pending", 0) + engine.get("failed", 0)
        if not (waiting or classify.get("pending") or promote.get("pending") or engine.get("done")):
            continue
        parts = [f"{waiting:,} waiting for the knowledge base", f"{engine.get('done', 0):,} ingested",
                 f"{engine.get('skipped', 0):,} skipped as spam/bulk"]
        if classify.get("pending"):
            parts.append(f"{classify['pending']:,} need a spam/work decision")
        if promote.get("pending"):
            parts.append(f"{promote['pending']:,} to distill into company knowledge (no PII)")
        if tab == "work":
            candidates = _candidate_count()
            if candidates:
                parts.append(f"{candidates:,} company-knowledge candidates ready to review for RTEC-HR")
        items.append({"id": f"intake:{tab}", "tab": tab, "kind": "intake_queue", "title": "Ingestion queue",
                      "why": "; ".join(parts), "source": "intake", "context": {"stats": stats}})
    return items


def _candidate_count() -> int:
    try:
        from agent_os.intake.promote import candidates_path

        path = candidates_path()
        return sum(1 for line in path.open(encoding="utf-8") if '"status": "candidate"' in line) if path.exists() else 0
    except Exception:  # noqa: BLE001
        return 0
