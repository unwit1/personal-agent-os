"""P2.3 planner context: the local repository map, the planner's exploration
budget, and tool-restricted read-only workers. No model calls."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator import OrchestratorFixture  # noqa: E402
from test_orchestrator_overhead import adapter, request  # noqa: E402

from agent_os.orchestrator import prompts, repomap  # noqa: E402
from agent_os.orchestrator.adapters import claude_code  # noqa: E402


def make_repo(root: Path) -> Path:
    files = {
        "src/billing/invoice.py": "def render_invoice(order):\n    return order\n\nclass InvoiceError(Exception):\n    pass\n",
        "src/billing/tax.py": "def vat_rate(country):\n    return 0.2\n",
        "src/shipping/labels.py": "def print_label(parcel):\n    return parcel\n",
        "tests/test_invoice.py": "from src.billing.invoice import render_invoice\n",
        "docs/billing.md": "# Billing\nInvoices include VAT.\n",
        "data/big.json": "{\"invoice\": 1}\n",
        "README.md": "# Shop\n",
        "schemas/invoice-v1.schema.json": "{\"type\": \"object\"}\n",
    }
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "init"]):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    return root


class RepoMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-map-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = make_repo(self.tmp)

    def test_ranks_relevant_files_with_defs_and_tests(self) -> None:
        result = repomap.build(self.repo, "Add a discount line to the invoice renderer and cover VAT rounding.")
        listed = [line[2:].split(" (")[0] for line in result["text"].splitlines()[2:]]
        self.assertEqual(listed[0], "src/billing/invoice.py")
        self.assertNotIn("src/shipping/labels.py", listed)
        self.assertIn("render_invoice, InvoiceError", result["text"])
        self.assertIn("[tests: tests/test_invoice.py]", result["text"])
        self.assertEqual(result["stats"]["tracked_files"], 8)

    def test_companion_files_are_listed(self) -> None:
        text = repomap.build(self.repo, "Add a discount line to the invoice renderer.", max_files=1)["text"]
        self.assertIn("Related by name", text)
        self.assertIn("schemas/invoice-v1.schema.json", text.splitlines()[-1])

    def test_explicit_path_mention_wins(self) -> None:
        result = repomap.build(self.repo, "Update `src/shipping/labels.py` so labels include the order id.")
        self.assertTrue(result["text"].splitlines()[2].startswith("- src/shipping/labels.py"))

    def test_roadmap_goal_uses_only_the_quoted_section(self) -> None:
        goal = "Continue the invoice roadmap: shipping would never match.\n\nRoadmap section:\n### P1 — Labels\nPrint parcel labels."
        listed = repomap.build(self.repo, goal)["text"]
        self.assertTrue(listed.splitlines()[2].startswith("- src/shipping/labels.py"))

    def test_bounded_size(self) -> None:
        self.assertLessEqual(len(repomap.build(self.repo, "invoice " * 50, max_chars=300)["text"]), 300)


class PlannerPromptTests(OrchestratorFixture):
    def test_budget_and_map_only_when_given(self) -> None:
        run = {"run_id": "r", "goal": "g", "policy": {"planner_read_budget": 5}, "nodes": {}}
        node = {"id": "plan", "role": "planner", "goal": "g", "context_budget": 1200}
        with_map, _ = prompts.build_measured(run, node, repo_map="Files most relevant to this goal:\n- a.py")
        without, _ = prompts.build_measured(run, node)
        self.assertIn("usually no more than 5", with_map)
        self.assertIn("- a.py", with_map)
        self.assertIn("do not re-read it", with_map)
        self.assertNotIn("repository map", without)
        self.assertIn("Read enough of the repository", without)

    def test_engine_builds_map_for_planner_when_enabled(self) -> None:
        run_id = self.engine.create_run("work on impl", repository=self.repo, policy=self.policy(planning="auto", planner_repo_map=True, default_validators=[{"kind": "command", "command": [sys.executable, "-c", "print(1)"]}]))["run_id"]
        self.engine.start(run_id)
        self.engine.step(run_id)
        prompt = (self.engine.store.run_dir(run_id) / "workers" / "plan-1" / "prompt.md").read_text(encoding="utf-8")
        self.assertIn("Repository layout", prompt)
        self.assertIn("Never read or edit the repository it is nested inside", prompt)
        events = [event for event in self.engine.ledger.read(run_id)[0] if event["type"] == "context_selected" and event["node"] == "plan"]
        self.assertTrue(any("repository map" in event["data"].get("method", "") for event in events))


class ReadOnlyModeTests(unittest.TestCase):
    def test_tools_mode_replaces_plan_mode_for_read_only_workers(self) -> None:
        argv = adapter(claude_code.ClaudeCodeAdapter, claude_code.OPTIONAL_FLAGS, read_only_mode="tools").resolve_invocation(request(read_only=True)).argv
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Glob,Grep", "no Bash, Edit or Write: read-only by construction")

    def test_tools_mode_does_not_touch_editing_workers(self) -> None:
        argv = adapter(claude_code.ClaudeCodeAdapter, claude_code.OPTIONAL_FLAGS, read_only_mode="tools").resolve_invocation(request()).argv
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
        self.assertIn("Edit", argv[argv.index("--tools") + 1])

    def test_plan_mode_remains_available(self) -> None:
        argv = adapter(claude_code.ClaudeCodeAdapter, claude_code.OPTIONAL_FLAGS, read_only_mode="plan").resolve_invocation(request(read_only=True)).argv
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "plan")


if __name__ == "__main__":
    unittest.main()
