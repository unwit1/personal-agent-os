"""Deterministic validator runner.

Validators decide whether work passed; an agent's report never does. Evidence
is compact (return code plus a short redacted tail), never a raw output dump.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .model import path_in_scope
from .store import redact


def run_validator(validator: dict[str, Any], cwd: Path | str, timeout: int = 900) -> dict[str, Any]:
    kind = validator.get("kind")
    label = validator.get("name") or kind
    if kind == "command":
        command = validator["command"]
        shell = isinstance(command, str)
        try:
            completed = subprocess.run(
                command if shell else [str(item) for item in command],
                cwd=str(cwd),
                shell=shell,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=int(validator.get("timeout_seconds", timeout)),
                stdin=subprocess.DEVNULL,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return {"name": label, "kind": "command", "passed": False, "returncode": None, "detail": redact(f"validator could not run: {error}", 400)}
        tail = (completed.stdout or "").strip().splitlines()[-3:] + (completed.stderr or "").strip().splitlines()[-2:]
        return {
            "name": label,
            "kind": "command",
            "passed": completed.returncode == 0,
            "returncode": completed.returncode,
            "detail": redact(" | ".join(tail), 400) or None,
        }
    if kind == "outputs_present":
        missing = [item for item in validator.get("outputs", []) if not (Path(cwd) / item).exists()]
        return {"name": label, "kind": kind, "passed": not missing, "detail": None if not missing else "missing: " + ", ".join(missing)}
    return {"name": label, "kind": "none", "passed": True, "detail": "no validator declared"}


def scope_check(changed: list[str], scope: list[str]) -> dict[str, Any]:
    outside = [path for path in changed if not path_in_scope(path, scope)]
    return {
        "name": "editable-scope",
        "kind": "scope",
        "passed": not outside,
        "detail": None if not outside else "edits outside declared scope: " + ", ".join(outside[:10]),
    }


def run_all(
    validators: list[dict[str, Any]],
    cwd: Path | str,
    *,
    changed: list[str] | None = None,
    scope: list[str] | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    if changed is not None:
        evidence.append(scope_check(changed, scope or []))
    for validator in validators:
        evidence.append(run_validator(validator, cwd, timeout))
    declared = [item for item in evidence if item["kind"] not in {"none", "scope"}]
    return {
        "passed": all(item["passed"] for item in evidence),
        "declared_validators": len(declared),
        "evidence": evidence,
    }
