"""Offline improvement lab on Harness² (google-research/harness2), Option C of DEC-0045.

Harness² proposes and composes candidate harnesses (Propose-Probe-Compose).
This module plugs the Orchestrator into its two seams and nothing else:

- ``ContextLabAdapter`` implements ``harness2.core.spec.BenchmarkAdapter``.
  The editable harness is the worker context-packet builder
  (``scripts/context.py``, seeded from ``prompts._context_packet``'s
  selection rule). ``execute`` runs that script in a subprocess with a
  scrubbed environment and no model. The deliverable is the packet.
- ``ScriptedProposer`` overrides ``Proposer.call``. It makes no model call:
  INV shortens the packet, DOM selects constraints that match the task, and
  composition applies both. Selection picks the candidate with the best
  scored outcome. That stands in for Harness²'s blind model pick and is
  labelled as such in the report.

Harness² executors, its ``claude`` channel and its third-party runners are
never imported. Promotion is not decided here: ``score`` is the
Orchestrator's own deterministic scorer, and results are evidence for
``orchestrator eval``, which keeps the promotion rules.

Run (Python 3.12+, harness2 importable, ideally with no network)::

    python -m orchestrator_os.lab_harness2 --out .agent-local/lab/context --k 2
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .usage import estimate_tokens

PINNED = "6868817518876de8fd170c6a8354daca273b6191"

# Mirrors prompts._context_packet: summary, then up to 8 constraints and 8
# validation commands, truncated to budget * 4 characters.
BASE_SCRIPT = '''import json, sys
task = json.load(open(sys.argv[1], encoding="utf-8"))
project, budget = task["project"], int(task.get("budget", 400))
lines = []
if project.get("summary"):
    lines.append("Project summary: " + project["summary"])
for key in ("constraints", "validation_commands"):
    values = project.get(key) or []
    if values:
        lines.append(key.replace("_", " ").capitalize() + ":")
        lines.extend("- " + item for item in values[:8])
print("\\n".join(lines)[: budget * 4])
'''

# Synthetic fixture: each task names the constraints a correct worker needs
# (``required``) among distractors. Held-out tasks are never shown to the
# proposer; the report scores them separately.
SUMMARY = ("Storefront monorepo with a Next.js web app, a Python pricing service, a shared design system, "
           "nightly data exports, and an internal admin console used by the support team on weekdays.")
CONSTRAINTS = [
    "pricing: never change currency rounding without a migration note",
    "web: keep bundle size under 250 kB per route",
    "admin: every new admin action needs an audit log entry",
    "exports: CSV columns are a public contract; add, never rename",
    "design-system: tokens change only through the tokens package",
    "pricing: discounts are applied before tax",
    "web: no new runtime dependencies without approval",
    "exports: timestamps are UTC ISO-8601",
    "admin: support role cannot delete customers",
    "tests: new code needs a unit test next to it",
]
VALIDATION = ["npm test --workspaces", "pytest services/pricing", "python tools/check_exports.py"]
TASKS = {
    "pricing-discount": ("dev", "Fix discount handling in the pricing service so percentage discounts apply before tax",
                         ["pricing: discounts are applied before tax", "pricing: never change currency rounding without a migration note",
                          "tests: new code needs a unit test next to it", "pytest services/pricing"]),
    "export-column": ("dev", "Add a refund_reason column to the nightly orders CSV export",
                      ["exports: CSV columns are a public contract; add, never rename", "exports: timestamps are UTC ISO-8601",
                       "python tools/check_exports.py"]),
    "admin-action": ("dev", "Add an admin action to resend a customer's invoice",
                     ["admin: every new admin action needs an audit log entry", "admin: support role cannot delete customers",
                      "tests: new code needs a unit test next to it"]),
    "web-widget": ("holdout", "Add a lightweight review widget to the product page of the web app",
                   ["web: keep bundle size under 250 kB per route", "web: no new runtime dependencies without approval",
                    "npm test --workspaces"]),
    "export-timezone": ("holdout", "Fix the export so order timestamps no longer use local server time",
                        ["exports: timestamps are UTC ISO-8601", "exports: CSV columns are a public contract; add, never rename",
                         "python tools/check_exports.py"]),
}


def score_packet(packet: str, required: list[str]) -> dict[str, Any]:
    """Recall of the facts the worker needs, and what they cost to send."""
    found = [item for item in required if item in packet]
    return {"recall": round(len(found) / len(required), 3), "missing": [item for item in required if item not in packet],
            "tokens": estimate_tokens(packet)}


def _require_harness2() -> Any:
    try:
        import harness2  # noqa: F401
        from harness2.core import proposer, schedule, spec, tree
        from harness2.substrate.opencode import OpencodeSubstrate
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise SystemExit(f"harness2 is not importable ({exc}); install the pinned extra: "
                         f"pip install 'git+https://github.com/google-research/harness2@{PINNED}'") from exc
    return proposer, schedule, spec, tree, OpencodeSubstrate


def build(root: Path) -> tuple[Any, Any, Any]:
    """Adapter and proposer classes bound to an installed harness2."""
    proposer_mod, schedule, spec, tree, OpencodeSubstrate = _require_harness2()

    class ContextLabAdapter:
        def __init__(self, root: Path, split: str = "dev") -> None:
            self.root, self.split = root, split
            self.substrate = OpencodeSubstrate()
            channel = spec.ChannelSpec("opencode", "local/deterministic")
            self.spec = spec.BenchSpec(name="orchestrator-context", runs_root=root / "runs", install_mode="workspace_config",
                                       prompts=spec.BenchPrompts(work="assemble the project context a coding worker needs"),
                                       channels={"proposer": channel, "selector": channel}, leak_globs=("required.json",))
            self.executions = 0
            base = {name: "" for name in self.substrate.surface().always_on}
            base["systemprompt.md"] = "Build the worker context packet with python scripts/context.py task.json.\n"
            base["scripts/context.py"] = BASE_SCRIPT
            tree.write_tree(self.substrate.surface(), base, self.base_harness(), stubs=False)
            for task_id, (_, goal, _) in TASKS.items():
                folder = self.task_files(task_id)
                folder.mkdir(parents=True, exist_ok=True)
                payload = {"goal": goal, "budget": 400,
                           "project": {"summary": SUMMARY, "constraints": CONSTRAINTS, "validation_commands": VALIDATION}}
                (folder / "task.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")

        def tasks(self, split: str = "all") -> list[str]:
            wanted = self.split if split == "all" else split
            return [task for task, (group, _, _) in TASKS.items() if wanted in ("all", group)]

        def domain_of(self, task_id: str) -> str:
            return "context"

        def task_prompt(self, task_id: str) -> str:
            return TASKS[task_id][1]

        def task_files(self, task_id: str) -> Path:
            return self.root / "sources" / task_id

        def base_harness(self) -> Path:
            return self.root / "base"

        def validate_tree(self, harness: Any) -> None:
            if "scripts/context.py" not in harness:
                raise ValueError("the context lab needs scripts/context.py")

        def execute(self, task_id: str, harness_dir: Path | None, run_id: str, *, timeout: int | None = None) -> Path:
            self.executions += 1
            run_dir = self.root / "executions" / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            script = (harness_dir or self.base_harness()) / "scripts/context.py"
            env = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8", "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
            result = subprocess.run([sys.executable, "-I", str(script), str(self.task_files(task_id) / "task.json")],
                                    capture_output=True, text=True, check=True, timeout=timeout or 20, env=env)
            (run_dir / "packet.md").write_text(result.stdout, encoding="utf-8")
            (run_dir / "trajectory.md").write_text("[ACTION] python scripts/context.py task.json\n[OBSERVATION]\n" + result.stdout, encoding="utf-8")
            return run_dir

        def delivered(self, run_dir: Path) -> bool:
            return (run_dir / "packet.md").is_file()

        def trajectory(self, run_dir: Path, *, obs_trunc: int) -> str:
            return (run_dir / "trajectory.md").read_text(encoding="utf-8")[: max(obs_trunc, 0) or None]

        def deliverable_text(self, run_dir: Path) -> str:
            return (run_dir / "packet.md").read_text(encoding="utf-8")

        def deliverable_files(self, run_dir: Path) -> dict[str, str]:
            return {"packet.md": self.deliverable_text(run_dir)}

        def score(self, task_id: str, run_dir: Path) -> dict[str, Any]:
            return score_packet(self.deliverable_text(run_dir), TASKS[task_id][2])

    class ScriptedProposer(proposer_mod.Proposer):
        """Deterministic stand-in for a model proposer: no model service is called."""

        def call(self, mission: Any, context_dir: Any, label: str, **kwargs: Any) -> Any:
            context = Path(context_dir)
            workspace = None
            if label.startswith("select."):
                task = json.loads((context / "source" / "task.json").read_text(encoding="utf-8"))
                needed = [c for c in CONSTRAINTS if _relevant(c, task["goal"])]
                candidates = sorted((context / "candidates").glob("*.md"))
                ranked = sorted(candidates, key=lambda p: (-sum(item in p.read_text(encoding="utf-8") for item in needed),
                                                           estimate_tokens(p.read_text(encoding="utf-8")), p.stem))
                text = (f"<why>Scripted stand-in for the blind model pick: most goal-relevant constraints, then fewest tokens."
                        f"</why>\n```choice\n{ranked[0].stem}\n```")
            elif label.startswith("experience."):
                text = ("<edits>\ncomponent: scripts/context.py\ncandidates: inv1, dom1\n"
                        "change: shorter summary; constraints filtered by goal keywords\n"
                        "observed: packet tokens fell while goal-relevant constraints stayed\nverdict: helped\n</edits>\n\n"
                        "<experience>\ncue: When a project lists many unrelated constraints\n"
                        "lesson: Send only constraints whose area matches the task, plus cross-cutting test rules.\n"
                        "evidence: scripted lab run; see the report's held-out rows before trusting it.\n"
                        "confidence: low (synthetic fixture)\n</experience>")
            else:
                workspace = context / "harness"
                script = workspace / "scripts" / "context.py"
                source = script.read_text(encoding="utf-8")
                # Harness2 stage labels: inv<i>, dom<i>, agg<i> (parallel), c<t> (sequential compose).
                kind = "inv" if label.startswith("inv") else "dom" if label.startswith("dom") else "agg"
                if kind in ("inv", "agg") and "SHORT_SUMMARY" not in source:
                    source = source.replace('lines.append("Project summary: " + project["summary"])',
                                            'lines.append("Project summary: " + project["summary"].split(",")[0])  # SHORT_SUMMARY')
                if kind in ("dom", "agg") and "TASK_FILTER" not in source:
                    source = source.replace('        lines.extend("- " + item for item in values[:8])',
                                            '        if key == "constraints":  # TASK_FILTER\n'
                                            '            words = {w.strip(".,:;").lower() for w in task["goal"].split()}\n'
                                            '            values = [v for v in values if v.split(":")[0] in words or v.split(":")[0] == "tests"'
                                            ' or any(w in v.lower() for w in words if len(w) > 4)]\n'
                                            '        lines.extend("- " + item for item in values[:8])')
                script.write_text(source, encoding="utf-8")
                text = f"<notes>{kind}: scripted edit of scripts/context.py</notes>"
            reply = proposer_mod.Reply(label=label, text=text, ok=True, attempts=1, workspace=workspace)
            self._calls.append(reply)
            return reply

    return ContextLabAdapter, ScriptedProposer, schedule


def _relevant(constraint: str, goal: str) -> bool:
    words = {w.strip(".,:;").lower() for w in goal.split()}
    area = constraint.split(":")[0]
    return area in words or area == "tests" or any(w in constraint.lower() for w in words if len(w) > 4)


def _variants() -> dict[str, str]:
    short = BASE_SCRIPT.replace('lines.append("Project summary: " + project["summary"])',
                                'lines.append("Project summary: " + project["summary"].split(",")[0])')
    filtered = BASE_SCRIPT.replace('        lines.extend("- " + item for item in values[:8])',
                                   '        if key == "constraints":\n'
                                   '            words = {w.strip(".,:;").lower() for w in task["goal"].split()}\n'
                                   '            values = [v for v in values if v.split(":")[0] in words or v.split(":")[0] == "tests"'
                                   ' or any(w in v.lower() for w in words if len(w) > 4)]\n'
                                   '        lines.extend("- " + item for item in values[:8])')
    return {"existing": BASE_SCRIPT, "shortened": short, "task_specific": filtered}


def _run_script(script: str, task_file: Path, scratch: Path) -> str:
    path = scratch / "context.py"
    path.write_text(script, encoding="utf-8")
    return subprocess.run([sys.executable, "-I", str(path), str(task_file)], capture_output=True, text=True, check=True, timeout=20).stdout


def run(out: Path, k: int = 2) -> dict[str, Any]:
    out = out.resolve()
    Adapter, Proposer, schedule = build(out)
    adapter = Adapter(out, split="dev")
    prop = Proposer(adapter.spec.channels["proposer"])
    result = schedule.run_domain("context", adapter.tasks("dev"), k, adapter=adapter, prop=prop, runs_root=adapter.spec.runs_root,
                                 library_root=out / "library" / f"k{k}", modes=("agg",))
    adopted = sorted((out / "library").rglob("scripts/context.py"))
    variants = _variants()
    if adopted:
        variants["harness2_composed"] = adopted[-1].read_text(encoding="utf-8")
    scratch = out / "variant-scratch"
    scratch.mkdir(exist_ok=True)
    rows = []
    for name, script in variants.items():
        for task_id, (group, _, required) in TASKS.items():
            packet = _run_script(script, adapter.task_files(task_id) / "task.json", scratch)
            rows.append({"variant": name, "task": task_id, "split": group, **score_packet(packet, required)})
    summary = {}
    for name in variants:
        for group in ("dev", "holdout"):
            picked = [row for row in rows if row["variant"] == name and row["split"] == group]
            summary.setdefault(name, {})[group] = {"recall": round(sum(r["recall"] for r in picked) / len(picked), 3),
                                                   "tokens": round(sum(r["tokens"] for r in picked) / len(picked), 1)}
    report = {"schema": "orchestrator-os/lab-harness2-context/v1", "harness2_commit": PINNED, "k": k, "model_calls": 0,
              "harness2": {"done": result.get("done"), "failed": result.get("failed"), "executions": adapter.executions,
                           "proposer_calls": len(prop._calls), "adopted_harness": [str(p.relative_to(out)) for p in adopted]},
              "selection": "scripted stand-in for Harness2's blind model pick (most goal-relevant constraints, then fewest tokens)",
              "caveat": "synthetic fixture; recall of named constraints is a proxy, not task success",
              "summary": summary, "rows": rows}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Harness2 context-construction lab (no model calls)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--k", type=int, default=2)
    args = parser.parse_args(argv)
    report = run(args.out, args.k)
    print(json.dumps({"summary": report["summary"], "harness2": report["harness2"]}, indent=2))
    return 0 if not report["harness2"]["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
