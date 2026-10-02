"""Keep a rented GPU busy: pick useful queued work and track paid idle time. Pure, no I/O beyond the checkpoint."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from . import free_swarm

DEFAULT_IDLE_TARGET = 0.15
WORKER_ROLES = frozenset({"implementer", "test_author", "repairer"})
DEFAULT_CLASSES = frozenset({"fast", "balanced"})
_STARTABLE = frozenset({"READY", "PENDING"})
_TERMINAL_RUN = frozenset({"PASSED", "FAILED", "FAILED_FINAL", "CANCELLED", "COMPLETED", "DONE"})


def _nodes(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    nodes = record.get("nodes") or []
    if isinstance(nodes, Mapping):
        nodes = nodes.values()
    return [n for n in nodes if isinstance(n, Mapping)]


def _item(record: Mapping[str, Any], node: Mapping[str, Any]) -> dict[str, Any]:
    return {"run_id": record.get("run_id") or record.get("id"), "node_id": node.get("id") or node.get("node_id"),
            "role": node.get("role"), "capability_class": node.get("capability_class"), "state": node.get("state")}


def useful_work(run_records: Iterable[Mapping[str, Any]], backfill_queue: Iterable[Mapping[str, Any]], *,
                roles: Iterable[str], classes: Iterable[str] | None = None,
                home: Path | None = None) -> dict[str, Any]:
    roles = set(roles or ())
    classes = set(DEFAULT_CLASSES if classes is None else classes)
    reviews: list[dict[str, Any]] = []
    workers: list[dict[str, Any]] = []
    for record in run_records or []:
        if not isinstance(record, Mapping) or str(record.get("status") or "").upper() in _TERMINAL_RUN:
            continue
        for node in _nodes(record):
            if node.get("state") not in _STARTABLE:
                continue
            role = node.get("role")
            if role == "reviewer" and "reviewer" in roles:
                reviews.append(_item(record, node))
            elif role in WORKER_ROLES and role in roles and node.get("capability_class") in classes:
                workers.append(_item(record, node))
    if reviews:
        return {"kind": "review", "items": reviews, "reason": f"{len(reviews)} reviewer node(s) ready"}
    if workers:
        return {"kind": "worker", "items": workers, "reason": f"{len(workers)} worker node(s) ready"}
    done = set(free_swarm.load_checkpoint(home)["done"])
    backfill = [i for i in backfill_queue or []
                if isinstance(i, Mapping) and i.get("id") is not None and str(i["id"]) not in done
                and i.get("kind") in free_swarm.BACKFILL_KINDS]
    if backfill:
        return {"kind": "backfill", "items": backfill, "reason": f"{len(backfill)} checkpointable backfill item(s)"}
    return {"kind": None, "items": [], "reason": "nothing useful queued"}


class PaidIdle:
    """Accumulates paid, idle and idle-while-work-was-queued seconds."""

    def __init__(self, paid_seconds: float = 0.0, idle_seconds: float = 0.0,
                 idle_with_work_seconds: float = 0.0) -> None:
        self.paid_seconds = float(paid_seconds)
        self.idle_seconds = float(idle_seconds)
        self.idle_with_work_seconds = float(idle_with_work_seconds)

    def tick(self, busy: bool, has_work: bool, seconds: float) -> None:
        seconds = max(0.0, float(seconds))
        self.paid_seconds += seconds
        if not busy:
            self.idle_seconds += seconds
            if has_work:
                self.idle_with_work_seconds += seconds

    def share(self) -> float:
        return self.idle_seconds / self.paid_seconds if self.paid_seconds > 0 else 0.0

    def meets_target(self, target: float = DEFAULT_IDLE_TARGET) -> bool:
        return self.share() <= target

    def to_dict(self) -> dict[str, float]:
        return {"paid_seconds": self.paid_seconds, "idle_seconds": self.idle_seconds,
                "idle_with_work_seconds": self.idle_with_work_seconds}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "PaidIdle":
        data = data or {}
        return cls(data.get("paid_seconds") or 0.0, data.get("idle_seconds") or 0.0,
                   data.get("idle_with_work_seconds") or 0.0)
