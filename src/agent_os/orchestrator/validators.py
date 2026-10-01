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
            completed = _run_tree(
                command if shell else [str(item) for item in command],
                cwd=str(cwd),
                shell=shell,
                timeout=int(validator.get("timeout_seconds", timeout)),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return {"name": label, "kind": "command", "passed": False, "returncode": None, "detail": redact(f"validator could not run: {error}", 400)}
        tail = (completed.stdout or "").strip().splitlines()[-3:] + (completed.stderr or "").strip().splitlines()[-2:]
        output = (completed.stdout or "") + chr(10) + (completed.stderr or "")
        result = {
            "name": label,
            "kind": "command",
            "passed": completed.returncode == 0,
            "returncode": completed.returncode,
            "detail": redact(" | ".join(tail), 400) or None,
            **test_counts(output),
        }
        if completed.returncode != 0:
            # Test names when a test runner ran; otherwise the command's error
            # signature, so a failure that already exists on the base commit
            # can still be recognised as pre-existing (engine baseline excuse).
            result["failed_tests"] = failed_tests(output) or error_signature(completed.stdout or "", completed.stderr or "", cwd)
        return result
    if kind == "outputs_present":
        missing = [item for item in validator.get("outputs", []) if not (Path(cwd) / item).exists()]
        return {"name": label, "kind": kind, "passed": not missing, "detail": None if not missing else "missing: " + ", ".join(missing)}
    return {"name": label, "kind": "none", "passed": True, "detail": "no validator declared"}


def _run_tree(command: Any, *, cwd: str, shell: bool, timeout: int) -> subprocess.CompletedProcess:
    """subprocess.run, except a timeout kills the whole process tree.

    With ``shell=True`` on Windows the child is ``cmd.exe``; killing only it
    leaves the real test process running and holding the output pipes, so
    the timeout would not end the wait."""
    process = subprocess.Popen(
        command, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        from .adapters.base import kill_tree

        kill_tree(process.pid)
        process.kill()
        process.communicate()
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


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


_UNITTEST_FAILURE = re.compile(r"^(?:FAIL|ERROR): (\S+) \(([^)\s]+)\)", re.MULTILINE)
_PYTEST_FAILURE = re.compile(r"^(?:FAILED|ERROR) (\S+::\S+)", re.MULTILINE)


_ERROR_LINE = re.compile(r"(error|errors|exception)\b|\btraceback\b|\bfail(ed|ure|ures)?\b", re.I)
_VOLATILE = re.compile(r"\b\d+(\.\d+)?\s*(s|ms|seconds)\b|0x[0-9a-f]+|\b\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+")


def error_signature(stdout: str, stderr: str, cwd: Path | str) -> list[str]:
    """Normalized error lines of a failing non-test command, prefixed
    ``error:``: the ``errors`` list of JSON output (e.g. ``agent.py validate``)
    when there is one, else error-like lines. Worktree paths, timings and
    addresses are normalized so the base commit and a change compare equal.
    Empty when nothing error-like is found (then nothing can be excused)."""
    import json as _json

    roots = {str(Path(cwd)), str(Path(cwd)).replace("\\", "/")}

    def clean(line: str) -> str:
        for root in roots:
            line = line.replace(root, "<worktree>")
        return _VOLATILE.sub("<n>", line).strip()[:240]

    lines: list[str] = []
    text = (stdout or "").strip()
    start = text.find("{")
    if start != -1:
        try:
            data = _json.loads(text[start:])
            if isinstance(data, dict) and isinstance(data.get("errors"), list):
                lines = [str(item) for item in data["errors"]]
        except ValueError:
            pass
    if not lines:
        lines = [line for line in (stdout + "\n" + stderr).splitlines() if _ERROR_LINE.search(line) and "Warning" not in line]
    return sorted({"error: " + clean(line) for line in lines if line.strip()})[:50]


def failed_tests(output: str) -> list[str]:
    """Sorted identities of failing tests (unittest or pytest); empty when none parse."""
    names = {match.group(2).split(".", 1)[-1] if match.group(2).startswith("tests.") else match.group(2) for match in _UNITTEST_FAILURE.finditer(output)}
    names.update(match.group(1) for match in _PYTEST_FAILURE.finditer(output))
    return sorted(names)


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
    control_plane: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """``control_plane`` (``{"allowed": [...]}``) enables the protected-path
    check of ``control_plane.py`` for runs that target this repository."""
    evidence: list[dict[str, Any]] = []
    if changed is not None:
        evidence.append(scope_check(changed, scope or []))
        if control_plane is not None:
            from .control_plane import check

            evidence.append(check(changed, control_plane.get("allowed") or []))
            if control_plane.get("base_commit"):
                from .control_plane import negative_evidence_check

                evidence.append(negative_evidence_check(cwd, control_plane["base_commit"], changed, control_plane.get("allowed") or []))
    for validator in validators:
        evidence.append(run_validator(validator, cwd, timeout))
    declared = [item for item in evidence if item["kind"] not in {"none", "scope"}]
    return {
        "passed": all(item["passed"] for item in evidence),
        "declared_validators": len(declared),
        "evidence": evidence,
    }
