"""IMP-0006: deterministic affected-test selection and the engine's
affected-tests-first validation step (full validators still gate)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.test_selection import ImportGraphSelector, affected_first_validator, runs_unit_tests  # noqa: E402

from test_orchestrator import OrchestratorFixture  # noqa: E402

CALC = "def add(a, b):\n    return a + b\n"
BROKEN = "def add(a, b):\n    return a - b\n"
TEST_CALC = "import unittest\nfrom agent_os.calc import add\n\n\nclass T(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 2), 4)\n"
TEST_OTHER = "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_other(self):\n        self.assertTrue(True)\n"
TEST_VIA = "import unittest\nfrom agent_os import wrapper\n\n\nclass T(unittest.TestCase):\n    def test_wrapper(self):\n        self.assertEqual(wrapper.double(2), 4)\n"
WRAPPER = "from .calc import add\n\n\ndef double(x):\n    return add(x, x)\n"


def write_tree(root: Path) -> None:
    (root / "src" / "agent_os").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "agent_os" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "agent_os" / "calc.py").write_text(CALC, encoding="utf-8")
    (root / "src" / "agent_os" / "wrapper.py").write_text(WRAPPER, encoding="utf-8")
    (root / "tests" / "__init__.py").write_text("import sys, pathlib\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))\n", encoding="utf-8")
    (root / "tests" / "test_calc.py").write_text(TEST_CALC, encoding="utf-8")
    (root / "tests" / "test_via.py").write_text(TEST_VIA, encoding="utf-8")
    (root / "tests" / "test_other.py").write_text(TEST_OTHER, encoding="utf-8")


class SelectorTests(unittest.TestCase):
    def test_transitive_selection_from_working_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_tree(root)
            selector = ImportGraphSelector(None, root)
            self.assertEqual(selector.select(["src/agent_os/calc.py"]), ["tests.test_calc", "tests.test_via"])
            self.assertEqual(selector.select(["src/agent_os/wrapper.py"]), ["tests.test_via"])
            self.assertEqual(selector.select(["tests/test_other.py"]), ["tests.test_other"])
            self.assertEqual(selector.select(["README.md"]), [])

    def test_affected_validator_and_unit_test_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_tree(root)
            step = affected_first_validator(["src/agent_os/calc.py"], root, sys.executable)
            self.assertEqual((step["name"], step["selected"], step["of"]), ("affected-tests", ["tests.test_calc", "tests.test_via"], 3))
            self.assertIsNone(affected_first_validator(["docs/x.md"], root, sys.executable))
        self.assertTrue(runs_unit_tests([{"kind": "command", "command": "python -m unittest discover -s tests"}]))
        self.assertFalse(runs_unit_tests([{"kind": "command", "command": [sys.executable, "-c", "print(1)"]}]))


class EngineAffectedFirstTests(OrchestratorFixture):
    def setUp(self) -> None:
        super().setUp()
        write_tree(self.repo)
        self.git("add", "-A")
        self.git("commit", "-m", "package and tests")
        self.project = {"kind": "command", "name": "project-validation-1", "command": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."]}

    def script(self, content: str):
        def run(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            return {"edits": {"src/agent_os/calc.py": content}, "structured": {"status": "done", "summary": "edited calc"}}
        return run

    def run_one(self, content: str, **policy) -> dict:
        for name in self.providers:
            synthetic.SCRIPTS[name] = self.script(content)
        run_id = self.create([self.task("calc", scope=["src"], validators=[self.project])], max_stage_retries=0, max_escalations=0, provider_failover=False, **policy)
        self.engine.run_loop(run_id, max_ticks=40)
        return self.node(run_id, "calc")

    def test_new_failure_in_affected_tests_fails_fast(self) -> None:
        node = self.run_one(BROKEN, affected_tests_first="always")
        validation = node["validation"]
        self.assertTrue(validation.get("fail_fast"))
        affected = [item for item in validation["evidence"] if item.get("name") == "affected-tests"][0]
        self.assertFalse(affected["passed"])
        self.assertEqual((affected["selected"], affected["of"]), (2, 3))
        # The full suite did not run for this attempt.
        self.assertNotIn("project-validation-1", [item.get("name") for item in validation["evidence"]])

    def test_passing_change_still_runs_the_full_validators(self) -> None:
        node = self.run_one("def add(a, b):\n    return b + a\n", affected_tests_first="always")
        names = [item.get("name") for item in node["validation"]["evidence"]]
        self.assertIn("affected-tests", names)
        self.assertIn("project-validation-1", names)
        self.assertTrue(node["validation"]["passed"])

    def test_default_skips_first_attempts(self) -> None:
        node = self.run_one(BROKEN)
        names = [item.get("name") for item in node["validation"]["evidence"]]
        self.assertNotIn("affected-tests", names)

    def test_policy_values(self) -> None:
        from agent_os.orchestrator.model import PolicyError, merge_policy

        self.assertEqual(merge_policy()["affected_tests_first"], "retries")
        self.assertEqual(merge_policy({"affected_tests_first": True})["affected_tests_first"], "always")
        with self.assertRaises(PolicyError):
            merge_policy({"affected_tests_first": "sometimes"})

    def test_policy_can_disable_the_step(self) -> None:
        node = self.run_one(BROKEN, affected_tests_first=False)
        names = [item.get("name") for item in node["validation"]["evidence"]]
        self.assertNotIn("affected-tests", names)
        self.assertIn("project-validation-1", names)


if __name__ == "__main__":
    unittest.main()
