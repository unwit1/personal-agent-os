"""IMP-0015: eval-queue runner plans, attribution guard and append-only status."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import evalqueue, radar  # noqa: E402
from agent_os.orchestrator.model_profile import endpoint_entry  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402

SUITES = ["EVS-CAPABILITY-CLASSIFICATION"]


class EvalQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        with radar.queue_path(self.home).open("w", encoding="utf-8") as handle:
            for model_id, suites in (("org/served", SUITES), ("org/inline-only", SUITES), ("org/absent", SUITES), ("org/audio", [])):
                handle.write(json.dumps({"model_id": model_id, "revision": "r1", "status": "queued", "suggested_suites": suites}) + "\n")
        served = endpoint_entry("local-a", base_url="http://127.0.0.1:8000", model="org/served", classes=["fast"], roles=["inline", "analyst"])
        inline = endpoint_entry("local-b", base_url="http://127.0.0.1:8001", model="org/inline-only", classes=["fast"])
        audio = endpoint_entry("local-c", base_url="http://127.0.0.1:8002", model="org/audio", classes=["fast"], roles=["inline", "analyst"])
        cloud = {"id": "cloud", "adapter": "synthetic", "models": {"fast": "cloud-fast"}, "costs": {"fast": 1}}
        self.registry = ProviderRegistry(providers=[served, inline, audio, cloud])

    def test_plan_explains_every_non_ready_job(self) -> None:
        jobs = {job["model_id"]: job for job in evalqueue.plan(registry=self.registry, home=self.home)}
        self.assertTrue(jobs["org/served"]["ready"])
        self.assertEqual((jobs["org/served"]["candidate"], jobs["org/served"]["incumbent"]), ("local-a:org/served@fast", "cloud:cloud-fast@fast"))
        self.assertIn("lacks role analyst", jobs["org/inline-only"]["reason"])
        self.assertIn("not served", jobs["org/absent"]["reason"])
        self.assertIn("no suite", jobs["org/audio"]["reason"])

    def run_with(self, result_provider: str | None = "local-a", raises: bool = False) -> list[dict]:
        def runner(suite, routes, samples, max_calls, write):
            if raises:
                raise RuntimeError("harness failed")
            self.assertEqual((routes, samples, max_calls, write), (["cloud:cloud-fast@fast", "local-a:org/served@fast"], 1, 6, True))
            return {"id": "EVR-9999", "outcome": "noninferior", "metrics": {"results": [
                {"ref": "cloud:cloud-fast@fast", "provider": "cloud", "accuracy": 0.7},
                {"ref": "local-a:org/served@fast", "provider": result_provider, "accuracy": 0.8, "model_resolved": "org/served"}]}}
        return evalqueue.run("org/served", registry=self.registry, home=self.home, runner=runner)

    def test_successful_run_is_recorded_and_not_replanned(self) -> None:
        outcome = self.run_with()[0]
        self.assertEqual((outcome["status"], outcome["evrs"][0]["accuracy"], outcome["evrs"][0]["evr"]), ("evaluated", 0.8, "EVR-9999"))
        self.assertEqual(evalqueue.current(self.home)[("org/served", "r1")]["status"], "evaluated")
        self.assertEqual([job for job in evalqueue.plan("org/served", registry=self.registry, home=self.home)], [])
        self.assertEqual(len(evalqueue.entries(self.home)), 5)  # append-only: the queued line is kept

    def test_wrong_provider_answering_marks_the_result_invalid(self) -> None:
        outcome = self.run_with(result_provider="cloud")[0]
        self.assertEqual(outcome["status"], "invalid")
        self.assertIn("not local-a", outcome["problems"][0])

    def test_harness_errors_are_recorded_and_retryable(self) -> None:
        outcome = self.run_with(raises=True)[0]
        self.assertEqual(outcome["status"], "error")
        self.assertTrue(evalqueue.plan("org/served", registry=self.registry, home=self.home)[0]["ready"])


if __name__ == "__main__":
    unittest.main()
