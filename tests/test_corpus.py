"""MIE-0019: external attack-corpus import (as data, never committed)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator import corpus  # noqa: E402

# A benign synthetic module in AgentDojo's shape (no real attack content).
SAMPLE = '''
from agentdojo.base_tasks import BaseInjectionTask

class InjectionTask0(BaseInjectionTask):
    DIFFICULTY = "EASY"
    GOAL = "PLACEHOLDER benign objective for tests"

class InjectionTask1(BaseInjectionTask):
    GOAL = "PLACEHOLDER second objective"

class NotAnInjection:
    GOAL = "ignored"
'''


class ParseTests(unittest.TestCase):
    def test_parses_injection_task_classes_only(self) -> None:
        tasks = corpus.parse_injection_tasks(SAMPLE)
        self.assertEqual([t["task"] for t in tasks], ["InjectionTask0", "InjectionTask1"])
        self.assertEqual(tasks[0]["difficulty"], "'EASY'")
        self.assertTrue(all("PLACEHOLDER" in t["goal"] for t in tasks))

    def test_bad_source_is_empty(self) -> None:
        self.assertEqual(corpus.parse_injection_tasks("def (:"), [])


class ImportTests(unittest.TestCase):
    def opener(self, *_a, **_k):
        class R:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False

            def read(self_inner):
                return SAMPLE.encode()

        return R()

    def test_import_writes_locally_only_and_summarizes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec = {"id": "XC-agentdojo", "repo": "x/y", "ref": "abc123", "paths": ["a/banking/injection_tasks.py", "a/slack/injection_tasks.py"]}
            summary = corpus.import_agentdojo(write=True, opener=self.opener, local_root=Path(tmp), spec=spec)
            self.assertTrue(summary["ok"])
            self.assertEqual(summary["injection_tasks"], 4)  # 2 suites x 2 tasks
            self.assertFalse(summary["committed"])
            local = Path(tmp) / "agentdojo"
            self.assertTrue((local / "banking.json").exists())
            self.assertTrue((local / "index.json").exists())

    def test_dry_run_fetches_nothing_to_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec = {"id": "XC-agentdojo", "repo": "x/y", "ref": "abc", "paths": ["a/banking/injection_tasks.py"]}
            summary = corpus.import_agentdojo(write=False, opener=self.opener, local_root=Path(tmp), spec=spec)
            self.assertEqual((summary["injection_tasks"], summary["local_ref"]), (2, None))
            self.assertFalse((Path(tmp) / "agentdojo").exists())

    def test_fetch_failure_is_reported(self) -> None:
        def boom(*_a, **_k):
            raise TimeoutError("network down")

        summary = corpus.import_agentdojo(write=False, opener=boom, spec={"id": "XC-agentdojo", "repo": "x/y", "ref": "a", "paths": ["p/injection_tasks.py"]})
        self.assertFalse(summary["ok"])
        self.assertIn("TimeoutError", summary["error"])

    def test_registry_update_records_provenance_not_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            reg = Path(tmp) / "corpora.json"
            reg.write_text(json.dumps({"corpora": [{"id": "XC-agentdojo", "status": "candidate"}]}), encoding="utf-8")
            summary = {"id": "XC-agentdojo", "ok": True, "ref": "abc123", "local_ref": str(Path(tmp) / "agentdojo"), "imported_at": "2026-09-29", "suites": [{"suite": "banking", "tasks": 2}]}
            corpus.apply_import_to_registry(summary, reg)
            entry = json.loads(reg.read_text(encoding="utf-8"))["corpora"][0]
            self.assertEqual((entry["status"], entry["revision"]), ("imported", "abc123"))
            self.assertNotIn("PLACEHOLDER", reg.read_text(encoding="utf-8"))


class GitignoreTests(unittest.TestCase):
    def test_local_corpora_path_is_gitignored(self) -> None:
        self.assertTrue(corpus.LOCAL_ROOT.is_relative_to(ROOT / ".agent-local"))


if __name__ == "__main__":
    unittest.main()
