"""Fake compute provider (IMP-0015 slice 2): in-memory test doubles for launch/poll/stop/terminate.

FakeProvider is injected via a factory protocol, never reached via network. The protocol
conforms to DEC-0042 / docs/model-infrastructure.md Gated provisioning interface.
Provider name: 'fake'.

Instance state is persisted to <home>/compute-providers/fake.json so provider instances
survive across calls (resume-safe, per R5-1).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .store import orchestrator_home
from ..storage import write_json


class FakeProvider:
    """Fake compute provider for testing and development. Instance state is persisted
    to disk; cost accrues while running and freezes at stop."""

    name = "fake"

    def __init__(self, hourly_usd: float = 1.0, clock: callable | None = None,
                 fail_launch: bool = False, home: Path | None = None) -> None:
        """Initialize FakeProvider.

        Args:
            hourly_usd: Cost per hour of runtime (default 1.0).
            clock: Time function returning seconds (default time.monotonic).
            fail_launch: If True, launch() creates the instance then raises.
            home: Path to orchestrator home for state persistence (default: orchestrator_home()).
        """
        self.hourly_usd = float(hourly_usd)
        self.clock = clock if clock is not None else time.monotonic
        self.fail_launch = fail_launch
        self.home = home or orchestrator_home()
        self._state_path = Path(self.home) / "compute-providers" / "fake.json"
        self._load_instances()

    def _load_instances(self) -> None:
        """Load persisted instance state from disk."""
        if self._state_path.exists():
            try:
                self.instances = json.loads(self._state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.instances = {}
        else:
            self.instances = {}

    def _save_instances(self) -> None:
        """Persist instance state to disk."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(self._state_path, self.instances)

    def _get_next_launch_id(self) -> int:
        """Get the next launch number from existing instances."""
        if not self.instances:
            return 1
        return max((int(iid.split("-")[1]) for iid in self.instances if iid.startswith("fake-")), default=0) + 1

    def _settle(self, instance: dict[str, Any], now: float) -> None:
        """Apply max_runtime deadline to instance. If deadline has passed, stop it."""
        if instance["state"] != "running":
            return
        max_runtime = instance.get("max_runtime_seconds")
        if max_runtime is None:
            return
        started_at = instance["started_at"]
        deadline = started_at + max_runtime
        if now >= deadline:
            instance["state"] = "stopped"
            instance["stopped_at"] = deadline

    def launch(self, spec: dict[str, Any]) -> dict[str, str]:
        """Launch an instance from spec.

        Args:
            spec: Dictionary with keys: name (job_id), gpu, hourly_usd, max_runtime_seconds, secret_ref (optional).

        Returns:
            Dictionary with 'instance_id'.

        Raises:
            RuntimeError: If fail_launch is set (after creating the instance).
        """
        now = self.clock()
        launch_num = self._get_next_launch_id()
        instance_id = f"fake-{launch_num}"
        self.instances[instance_id] = {
            "name": spec.get("name"),
            "state": "running",
            "started_at": now,
            "stopped_at": None,
            "terminated_at": None,
            "hourly_usd": self.hourly_usd,
            "max_runtime_seconds": spec.get("max_runtime_seconds"),
        }
        self._save_instances()

        if self.fail_launch:
            raise RuntimeError(f"Simulated launch failure for {instance_id}")

        return {"instance_id": instance_id}

    def poll(self, instance_id: str) -> dict[str, Any]:
        """Poll instance state and cost.

        Args:
            instance_id: Instance identifier from launch().

        Returns:
            Dictionary with 'state' (running|stopped|terminated), 'runtime_seconds', 'cost_usd'.

        Raises:
            KeyError: If instance_id does not exist.
        """
        if instance_id not in self.instances:
            raise KeyError(f"unknown instance {instance_id}")

        instance = self.instances[instance_id]
        now = self.clock()
        self._settle(instance, now)

        if instance["state"] in ("stopped", "terminated"):
            runtime = instance["stopped_at"] - instance["started_at"]
        else:
            runtime = now - instance["started_at"]

        runtime = max(0.0, runtime)
        cost = runtime / 3600.0 * self.hourly_usd

        return {
            "state": instance["state"],
            "runtime_seconds": runtime,
            "cost_usd": cost,
        }

    def stop(self, instance_id: str) -> None:
        """Stop an instance. Idempotent. Respects max_runtime deadline.

        Args:
            instance_id: Instance identifier from launch().

        Raises:
            KeyError: If instance_id does not exist.
        """
        if instance_id not in self.instances:
            raise KeyError(f"unknown instance {instance_id}")

        instance = self.instances[instance_id]
        now = self.clock()
        self._settle(instance, now)

        if instance["state"] == "running":
            instance["stopped_at"] = now
            instance["state"] = "stopped"
            self._save_instances()

    def terminate(self, instance_id: str) -> None:
        """Terminate an instance. Idempotent. Respects max_runtime deadline.

        Args:
            instance_id: Instance identifier from launch().

        Raises:
            KeyError: If instance_id does not exist.
        """
        if instance_id not in self.instances:
            raise KeyError(f"unknown instance {instance_id}")

        instance = self.instances[instance_id]
        now = self.clock()
        self._settle(instance, now)

        if instance["state"] != "terminated":
            if instance["state"] == "running" and instance["stopped_at"] is None:
                instance["stopped_at"] = now
            instance["terminated_at"] = now
            instance["state"] = "terminated"
            self._save_instances()
