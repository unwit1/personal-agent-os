"""Deterministic validator runner.

Validators decide whether work passed; an agent's report never does. Evidence
is compact (return code plus a short redacted tail), never a raw output dump.
"""

from __future__ import annotations

import os
import re
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
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
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
            **test_counts((completed.stdout or "") + chr(10) + (completed.stderr or "")),
        }
    if kind == "outputs_present":
        missing = [item for item in validator.get("outputs", []) if not (Path(cwd) / item).exists()]
        return {"name": label, "kind": kind, "passed": not missing, "detail": None if not missing else "missing: " + ", ".join(missing)}
    return {"name": label, "kind": "none", "passed": True, "detail": "no validator declared"}


_UNITTEST_RAN = re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE)
_UNITTEST_FAILED = re.compile(r"^FAILED \(([^)]*)\)", re.MULTILINE)
_PYTEST_COUNT = re.compile(r"(\d+) (passed|failed|errors?)\b")
_PYTEST_SUMMARY = re.compile(r"^=+ .*\b(?:passed|failed|errors?)\b.* in [\d.]+s.*=+$", re.MULTILINE)


def test_counts(output: str) -> dict[str, int]:
    """Test totals from unittest or pytest output; empty when neither ran."""
    ran = _UNITTEST_RAN.findall(output)
    if ran:
        total = sum(int(item) for item in ran)
        failed = 0
        for summary in _UNITTEST_FAILED.findall(output):
            failed += sum(int(value) for key, value in re.findall(r"(failures|errors)=(\d+)", summary))
        return {"tests_run": total, "tests_failed": failed, "tests_passed": max(total - failed, 0)}
    summaries = _PYTEST_SUMMARY.findall(output)
    counts: dict[str, int] = {}
    for value, key in _PYTEST_COUNT.findall(summaries[-1] if summaries else ""):
        key = "error" if key.startswith("error") else key
        counts[key] = counts.get(key, 0) + int(value)
    if counts:
        failed = counts.get("failed", 0) + counts.get("error", 0)
        passed = counts.get("passed", 0)
        return {"tests_run": passed + failed, "tests_failed": failed, "tests_passed": passed}
    return {}


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
