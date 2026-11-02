"""Fake compute provider (IMP-0015 slice 2): in-memory test doubles for launch/poll/stop/terminate.

FakeProvider is injected via a factory protocol, never reached via network. The protocol
conforms to DEC-0043 / docs/model-infrastructure.md Gated provisioning interface.
Provider name: 'fake'. With state_path set, state persists as JSON so it survives new processes.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Callable


class FakeProvider:
    """Fake compute provider for testing and development. Instance lifecycle is in-memory;
    cost accrues while running and freezes at stop."""

    name = "fake"

    def __init__(self, hourly_usd: float = 1.0, clock: Callable[[], float] | None = None,
                 fail_launch: bool = False, state_path: Path | None = None) -> None:
        """Initialize FakeProvider.

        Args:
            hourly_usd: Cost per hour of runtime (default 1.0).
            clock: Time function returning seconds (default time.monotonic).
            fail_launch: If True, launch() creates the instance then raises.
            state_path: Optional JSON file holding {'launches', 'instances'}. Loaded on init when
                present and rewritten atomically after every mutation. None keeps state in memory.
        """
        self.hourly_usd = float(hourly_usd)
        self.clock = clock if clock is not None else time.monotonic
        self.fail_launch = fail_launch
        self.launches = 0
        self.instances: dict[str, dict[str, Any]] = {}
        self.state_path = Path(state_path) if state_path is not None else None
        if self.state_path is not None and self.state_path.exists():
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.launches = int(data.get("launches", 0))
            self.instances = dict(data.get("instances", {}))

    def _persist(self) -> None:
        """Atomically write state to state_path (temp file next to it, then os.replace)."""
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"launches": self.launches, "instances": self.instances}, indent=2, sort_keys=True)
        fd, tmp = tempfile.mkstemp(prefix=self.state_path.name + ".", suffix=".tmp", dir=self.state_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp, self.state_path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

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

        Launch-or-lookup: if an instance with the same spec 'name' already exists (including one
        created by a launch that then raised), its id is returned and nothing new is created.

        Raises:
            RuntimeError: If fail_launch is set (after creating the instance). A lookup hit never raises.
        """
        name = spec.get("name")
        if name:
            existing = self.lookup(name)
            if existing is not None:
                return {"instance_id": existing}
        now = self.clock()
        self.launches += 1
        instance_id = f"fake-{self.launches}"
        self.instances[instance_id] = {
            "name": spec.get("name"),
            "state": "running",
            "started_at": now,
            "stopped_at": None,
            "terminated_at": None,
            "hourly_usd": float(spec["hourly_usd"]) if "hourly_usd" in spec else self.hourly_usd,
            "max_runtime_seconds": spec.get("max_runtime_seconds"),
        }
        self._persist()

        if self.fail_launch:
            raise RuntimeError(f"Simulated launch failure for {instance_id}")

        return {"instance_id": instance_id}

    def lookup(self, name: str) -> str | None:
        """Return the instance_id of an existing instance whose spec name equals `name`, or None."""
        for instance_id, instance in self.instances.items():
            if instance["name"] == name:
                return instance_id
        return None

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
        before = instance["state"]
        self._settle(instance, now)
        if instance["state"] != before:
            self._persist()

        if instance["state"] in ("stopped", "terminated"):
            runtime = instance["stopped_at"] - instance["started_at"]
        else:
            runtime = now - instance["started_at"]

        runtime = max(0.0, runtime)
        cost = runtime / 3600.0 * instance["hourly_usd"]

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
        self._persist()

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
        self._persist()
