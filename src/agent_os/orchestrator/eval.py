"""Incumbent-vs-candidate evaluation: ``agent-os orchestrate eval`` (IMP-0003).

A suite is an EVS record in ``projects/personal-agent-os/orchestrator-os/
evals/suites/``, always read from the trusted checkout running Agent OS
(``ROOT``), never from a candidate. Its ``metrics.runners`` decide how it runs:

* ``tests/*.py`` -- **test runner.** Each ref (commit, branch or tag) is checked
  out in its own detached worktree; the runner files are then overwritten with
  the trusted checkout's copies, so a candidate cannot weaken the test that
  judges it. Dimensions: tests run, passed, failures, errors, pass rate,
  seconds, and the names of failing tests.
* ``.../evals/cases/<split>/*.json`` -- **delegate cases.** Each ref is a
  *route* (``provider[:model][@class]``). The cases are answered through
  ``orchestrate delegate`` in a worktree pinned to the case file's
  ``base_commit`` (FND-0002) and scored against the labels. Dimensions:
  accuracy, contract pass, cost, seconds, input tokens.

Dimensions stay separate; there is no blended score. Each dimension gets a
delta and, where a direction is defined, a verdict (improved / noninferior /
regressed) using policy ``promotion.noninferiority_margin_default``. One EVR
record is written per suite run. Protected-holdout splits are refused unless
the operator passes ``--operator-holdout``.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from ..paths import ROOT
from ..timestamps import utc_now_iso
from . import capability
from .control_plane import load_policy
from .delegate import delegate
from .store import orchestrator_home

SUITES = ROOT / "projects" / "personal-agent-os" / "orchestrator-os" / "evals" / "suites"
EVALUATIONS = ROOT / "projects" / "personal-agent-os" / "orchestrator-os" / "records" / "evaluations"
BACKLOG = ROOT / "projects" / "personal-agent-os" / "research" / "meta-improvement" / "improvement-backlog.json"
HOLDOUT_SPLITS = {"protected_holdout", "rolling_private"}
_RAN = re.compile(r"^Ran (\d+) tests? in ([\d.]+)s", re.M)
_COUNTS = re.compile(r"(failures|errors|skipped)=(\d+)")
_FAILED = re.compile(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", re.M)
_EVR = re.compile(r"^EVR-(\d{4,})\.json$")
# git serializes worktree metadata with a lock file; parallel adds would race.
_WORKTREE_LOCK = threading.Lock()


class EvalError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Suites and refs
# ---------------------------------------------------------------------------


def load_suite(suite_id: str, directory: Path | None = None) -> dict[str, Any]:
    path = Path(directory or SUITES) / f"{suite_id}.json"
    try:
        suite = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalError(f"unknown or unreadable suite {suite_id}: {exc}") from exc
    if suite.get("type") != "EVS":
        raise EvalError(f"{suite_id} is not an EVS record")
    return suite


def classify_runner(runner: str) -> str:
    runner = runner.replace("\\", "/")
    if runner.startswith("tests/") and runner.endswith(".py"):
        return "tests"
    if "/evals/cases/" in runner and runner.endswith(".json"):
        return "cases"
    return "unsupported"


def check_holdout(suite: dict[str, Any], cases: list[dict[str, Any]], operator_holdout: bool) -> None:
    splits = set((suite.get("metrics") or {}).get("splits") or []) | {str(item.get("split")) for item in cases}
    runners = (suite.get("metrics") or {}).get("runners") or []
    touches = bool(splits & HOLDOUT_SPLITS) or any("/evals/holdout/" in str(item).replace("\\", "/") for item in runners)
    if touches and not operator_holdout:
        raise EvalError("suite uses a protected holdout split; only the operator may run it (--operator-holdout)")


def parse_route(spec: str) -> dict[str, str | None]:
    """``provider[:model][@class]`` -> route dict."""
    capability_class = None
    if "@" in spec:
        spec, capability_class = spec.rsplit("@", 1)
    provider, _, model = spec.partition(":")
    return {"spec": f"{provider}{':' + model if model else ''}{'@' + capability_class if capability_class else ''}", "provider": provider or None, "model": model or None, "capability_class": capability_class}


def _git(args: list[str], cwd: Path | str = ROOT, check: bool = True) -> str:
    completed = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
    if check and completed.returncode != 0:
        raise EvalError(f"git {' '.join(args)}: {completed.stderr.strip()[:300]}")
    return completed.stdout.strip()


def resolve_commit(ref: str) -> str:
    return _git(["rev-parse", "--verify", f"{ref}^{{commit}}"])


class Worktree:
    """Detached, throwaway worktree of the trusted repository. Kept under the
    orchestrator home, not %TEMP% (the Codex Windows sandbox refuses there)."""

    def __init__(self, commit: str) -> None:
        self.commit = commit
        self.path = orchestrator_home() / "eval-worktrees" / f"{commit[:10]}-{uuid.uuid4().hex[:6]}"

    def __enter__(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _WORKTREE_LOCK:
            _git(["worktree", "add", "--detach", str(self.path), self.commit])
        return self.path

    def __exit__(self, *exc: Any) -> None:
        with _WORKTREE_LOCK:
            _git(["worktree", "remove", "--force", str(self.path)], check=False)
            shutil.rmtree(self.path, ignore_errors=True)
            _git(["worktree", "prune"], check=False)


# ---------------------------------------------------------------------------
# Test-runner suites
# ---------------------------------------------------------------------------


def parse_unittest(output: str, returncode: int) -> dict[str, Any]:
    ran = _RAN.search(output)
    counts = {key: 0 for key in ("failures", "errors", "skipped")}
    tail = output[ran.end():] if ran else output
    for key, value in _COUNTS.findall(tail):
        counts[key] = int(value)
    tests = int(ran.group(1)) if ran else 0
    failed = sorted({f"{name} ({where})" for name, where in _FAILED.findall(output)})
    if not ran:
        counts["errors"] = max(counts["errors"], 1)
        failed = failed or [f"runner did not complete (exit {returncode})"]
    passed = max(tests - counts["failures"] - counts["errors"] - counts["skipped"], 0)
    return {"tests_run": tests, "passed": passed, **counts, "pass_rate": round(passed / tests, 4) if tests else 0.0, "failing": failed}


def run_tests_for_ref(ref: str, runners: list[str], timeout: int = 1800) -> dict[str, Any]:
    commit = resolve_commit(ref)
    modules = [runner[:-3].replace("/", ".") for runner in runners]
    with Worktree(commit) as tree:
        # The judge comes from the trusted checkout, never from the candidate.
        for runner in runners:
            target = tree / runner
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / runner, target)
        started = time.monotonic()
        completed = subprocess.run([sys.executable, "-m", "unittest", *modules], cwd=tree, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        seconds = round(time.monotonic() - started, 2)
    result = parse_unittest(completed.stdout + "\n" + completed.stderr, completed.returncode)
    return {"ref": ref, "commit": commit[:12], "seconds": seconds, **result}


# ---------------------------------------------------------------------------
# Delegate-case suites
# ---------------------------------------------------------------------------


def _mie_prompt(case_file: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    items = {item["id"]: item for item in json.loads(BACKLOG.read_text(encoding="utf-8"))["items"]}
    ids = [case["input_ref"] for case in case_file["cases"]]
    lines = "\n".join(f"- {key}: {items[key]['title']} — {items[key]['proposed_change'][:220]}" for key in ids)
    prompt = (
        "Repository: the current working directory (Personal Agent OS, Python package src/agent_os).\n"
        "Task: for each backlog item below, determine whether the repository ALREADY implements it. Search code in "
        "src/agent_os/**, schemas/**, docs/**, tests/** (ignore projects/personal-agent-os/research/**). Use grep/rg; read only what you need.\n\n"
        f"Items:\n{lines}\n\n"
        "Classify each item as implemented | partial | missing. Evidence must be real repo-relative file paths that exist "
        "(optionally 'path:symbol'). If nothing found, status is missing and evidence is [].\n"
        'Result object: {"items":[{"id":"MIE-0001","status":"partial","evidence":["src/agent_os/improvements.py:capture"],"gap":"one sentence"}]}\n'
    )
    contract = {"required": {"items": "array"}, "items": {"min_items": len(ids), "expected_ids": ids, "required": {"id": "string", "status": "string", "evidence": "array"}, "enums": {"status": ["implemented", "partial", "missing"]}}}
    return prompt, contract


# Prompt builders per task family: evaluator code, kept out of case files so
# case files stay pure data (labels).
PROMPT_BUILDERS = {"research_implementation_classification": _mie_prompt}


def score_cases(result: dict[str, Any] | None, cases: list[dict[str, Any]]) -> dict[str, Any]:
    answers = {str(item.get("id")): item.get("status") for item in ((result or {}).get("items") or []) if isinstance(item, dict)}
    wrong = [{"id": case["input_ref"], "expected": case["expected_status"], "got": answers.get(case["input_ref"])} for case in cases if answers.get(case["input_ref"]) != case["expected_status"]]
    return {"cases": len(cases), "correct": len(cases) - len(wrong), "accuracy": round((len(cases) - len(wrong)) / len(cases), 4) if cases else 0.0, "wrong": wrong}


def run_cases_for_route(route: dict[str, Any], case_file: dict[str, Any], tree: Path, *, floor: float, timeout: int = 900, registry: Any = None) -> dict[str, Any]:
    builder = PROMPT_BUILDERS.get(case_file["task_family"])
    if builder is None:
        raise EvalError(f"no prompt builder for task family {case_file['task_family']}")
    prompt, contract = builder(case_file)
    outcome = delegate(prompt, task_family=case_file["task_family"], capability_class=route.get("capability_class") or "fast", effort="low", contract=contract, provider=route.get("provider"), model=route.get("model"), cwd=tree, timeout_seconds=timeout, record=False, registry=registry)
    usage = outcome.get("usage") or {}
    score = score_cases(outcome.get("result"), case_file["cases"]) if outcome["status"] == "passed" else {"cases": len(case_file["cases"]), "correct": 0, "accuracy": None, "wrong": []}
    selection = outcome.get("selection") or {}
    failure = None if outcome["status"] == "passed" else (outcome.get("errors") or ["unknown"])[0][:160]
    # FND-0001: the observation passes only when accuracy clears the floor, not
    # merely when the output had the right shape.
    capability.record_observation({
        "call_id": outcome["id"], "task_family": case_file["task_family"], "role": "analyst", "provider": selection.get("provider"),
        "model": selection.get("model"), "model_resolved": outcome.get("model_resolved"), "capability_class": selection.get("capability_class"),
        "effort": "low", "toolset": "read_only", "status": outcome["status"],
        "validator_passed": bool(score["accuracy"] is not None and score["accuracy"] >= floor), "contract_passed": outcome["status"] == "passed",
        "accuracy": score["accuracy"], "repairs": 0,
        "failure_type": failure or (None if score["accuracy"] is not None and score["accuracy"] >= floor else f"accuracy_below_floor: {score['accuracy']}"),
        "seconds": outcome.get("seconds"), "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
        "cost_usd": usage.get("cost_usd"), "usage_accuracy": usage.get("accuracy"), "eval_case_file": case_file.get("suite"), "base_commit": case_file.get("base_commit"), "at": utc_now_iso(),
    })
    return {
        "ref": route["spec"], "provider": selection.get("provider"), "model_resolved": outcome.get("model_resolved"), "status": outcome["status"],
        "failure": failure, "contract_pass": outcome["status"] == "passed", **score, "seconds": outcome.get("seconds"),
        "input_tokens": usage.get("input_tokens"), "cost_usd": usage.get("cost_usd"), "delegation": outcome["id"],
    }


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

# direction: +1 higher is better, -1 lower is better, 0 informational.
DIMENSIONS = {
    "tests": {"pass_rate": 1, "failures": -1, "errors": -1, "tests_run": 0, "seconds": -1},
    "cases": {"accuracy": 1, "contract_pass": 1, "cost_usd": -1, "seconds": -1, "input_tokens": -1},
}


def verdict(direction: int, incumbent: Any, candidate: Any, margin: float, relative: bool) -> str | None:
    if direction == 0 or not isinstance(incumbent, (int, float)) or not isinstance(candidate, (int, float)):
        return None
    incumbent, candidate = float(incumbent), float(candidate)
    better = (candidate - incumbent) * direction
    tolerance = abs(incumbent) * margin if relative else margin
    if better > tolerance:
        return "improved"
    if better >= -tolerance:
        return "noninferior"
    return "regressed"


def compare(kind: str, incumbent: dict[str, Any], candidate: dict[str, Any], margin: float) -> dict[str, Any]:
    dims = {}
    for name, direction in DIMENSIONS[kind].items():
        a, b = incumbent.get(name), candidate.get(name)
        a = float(a) if isinstance(a, bool) else a
        b = float(b) if isinstance(b, bool) else b
        # Rates use an absolute margin; costs/latency a relative one.
        relative = name in {"cost_usd", "seconds", "input_tokens"}
        dims[name] = {
            "incumbent": a, "candidate": b,
            "delta": round(b - a, 6) if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None,
            "verdict": verdict(direction, a, b, margin if not relative else max(margin, 0.10), relative),
        }
    if kind == "tests":
        new_failures = sorted(set(candidate.get("failing") or []) - set(incumbent.get("failing") or []))
        dims["new_failing_tests"] = {"candidate": new_failures, "verdict": "regressed" if new_failures else "noninferior"}
    return dims


def primary_verdict(kind: str, dims: dict[str, Any]) -> str:
    """Quality gate only: pass rate / accuracy, plus no new failing tests.
    Cost and latency are reported, never folded into this verdict."""
    key = "pass_rate" if kind == "tests" else "accuracy"
    result = dims[key]["verdict"] or "inconclusive"
    if kind == "tests" and dims["new_failing_tests"]["verdict"] == "regressed":
        return "regressed"
    return result


# ---------------------------------------------------------------------------
# EVR records
# ---------------------------------------------------------------------------


def next_evr_id(directory: Path | None = None) -> str:
    numbers = [int(match.group(1)) for path in Path(directory or EVALUATIONS).glob("EVR-*.json") if (match := _EVR.match(path.name))]
    return f"EVR-{(max(numbers) + 1 if numbers else 1):04d}"


def write_evr(record: dict[str, Any], directory: Path | None = None) -> str:
    target = Path(directory or EVALUATIONS)
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{record['id']}.json"
    if path.exists():
        raise EvalError(f"{path.name} exists; EVR records are append-only")
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def build_evr(suite: dict[str, Any], kind: str, results: list[dict[str, Any]], incumbent_ref: str, margin: float, evr_id: str, notes: list[str]) -> dict[str, Any]:
    incumbent = next(item for item in results if item["ref"] == incumbent_ref)
    comparisons = {}
    for candidate in results:
        if candidate is incumbent:
            continue
        dims = compare(kind, incumbent, candidate, margin)
        comparisons[candidate["ref"]] = {"verdict": primary_verdict(kind, dims), "dimensions": dims}
    verdicts = {item["verdict"] for item in comparisons.values()}
    outcome = "regressed" if "regressed" in verdicts else "improved" if verdicts == {"improved"} else "noninferior" if verdicts and verdicts <= {"improved", "noninferior"} else "inconclusive"
    stamp = utc_now_iso()
    links = [{"rel": "measures", "ref": f"projects/personal-agent-os/orchestrator-os/evals/suites/{suite['id']}.json"}, {"rel": "baseline", "ref": _ref_link(kind, incumbent)}]
    links += [{"rel": "candidate", "ref": _ref_link(kind, item)} for item in results if item is not incumbent]
    return {
        "schema": "personal-agent/evidence-record/v1", "id": evr_id, "type": "EVR",
        "title": f"{suite['id']}: {incumbent_ref} vs {', '.join(item['ref'] for item in results if item is not incumbent)}"[:200],
        "status": "accepted", "outcome": outcome,
        "summary": f"`agent-os orchestrate eval` ({kind} suite). Quality verdict per candidate uses {'pass rate + new failing tests' if kind == 'tests' else 'accuracy'}; cost and latency are reported separately. Noninferiority margin {margin}.",
        "task_family": ",".join((suite.get("metrics") or {}).get("task_families") or []),
        "metrics": {"kind": kind, "incumbent": incumbent_ref, "noninferiority_margin": margin, "results": results, "comparisons": comparisons, "notes": notes},
        "links": links,
        "provenance": {"source": "agent-os orchestrate eval", "suite_read_from": "trusted checkout", "trusted_commit": _git(["rev-parse", "--short", "HEAD"], check=False)},
        "created_at": stamp, "updated_at": stamp,
    }


def _ref_link(kind: str, result: dict[str, Any]) -> str:
    return f"commit:{result['commit']}" if kind == "tests" else f"local:route/{result['ref']}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(suite_id: str, *, incumbent: str | None = None, candidates: list[str] | None = None, routes: list[str] | None = None,
        operator_holdout: bool = False, write: bool = True, margin: float | None = None, parallel: bool = True) -> dict[str, Any]:
    suite = load_suite(suite_id)
    runners = [str(item) for item in (suite.get("metrics") or {}).get("runners") or []]
    kinds = {classify_runner(item) for item in runners}
    policy = load_policy()
    margin = float(margin if margin is not None else (policy.get("promotion") or {}).get("noninferiority_margin_default", 0.02))
    floor_map = (policy.get("routing") or {}).get("reliability_floor") or {}
    notes = [f"skipped unsupported runner {item}" for item in runners if classify_runner(item) == "unsupported"]
    if "cases" in kinds and "tests" in kinds:
        raise EvalError(f"{suite_id} mixes test runners and case files; split the suite")
    if "cases" in kinds:
        case_files = [json.loads((ROOT / item).read_text(encoding="utf-8")) for item in runners if classify_runner(item) == "cases"]
        check_holdout(suite, case_files, operator_holdout)
        specs = list(routes or [])
        if incumbent and incumbent not in specs:
            specs.insert(0, incumbent)
        if len(specs) < 2:
            raise EvalError("case suites need at least two routes (--route provider[:model][@class]); the first or --incumbent is the baseline")
        parsed = [parse_route(item) for item in specs]
        incumbent_ref = parse_route(incumbent)["spec"] if incumbent else parsed[0]["spec"]
        results: list[dict[str, Any]] = []
        for case_file in case_files:
            floor = float(floor_map.get(case_file["task_family"], floor_map.get("classification", floor_map.get("default", 0.9))))
            with Worktree(resolve_commit(case_file["base_commit"])) as tree:
                with ThreadPoolExecutor(max_workers=len(parsed) if parallel else 1) as pool:
                    results = list(pool.map(lambda route: run_cases_for_route(route, case_file, tree, floor=floor), parsed))
        kind = "cases"
    elif "tests" in kinds:
        check_holdout(suite, [], operator_holdout)
        if not candidates:
            raise EvalError("test suites need --candidate <ref> (and optionally --incumbent <ref>, default main)")
        incumbent_ref = incumbent or "main"
        test_runners = [item for item in runners if classify_runner(item) == "tests"]
        refs = [incumbent_ref, *[item for item in candidates if item != incumbent_ref]]
        with ThreadPoolExecutor(max_workers=len(refs) if parallel else 1) as pool:
            results = list(pool.map(lambda ref: run_tests_for_ref(ref, test_runners), refs))
        kind = "tests"
    else:
        raise EvalError(f"{suite_id} has no runnable runners ({', '.join(runners) or 'none'})")
    record = build_evr(suite, kind, results, incumbent_ref, margin, next_evr_id(), notes)
    record["written"] = write_evr({key: value for key, value in record.items() if key != "written"}) if write else None
    return record
