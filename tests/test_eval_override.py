"""IMP-0017 / FND-0014: an eval route whose provider override is not honoured
fails loudly and records no capability observation for the wrong provider."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import eval as evaluation  # noqa: E402

CASE_FILE = {"task_family": "unit_family", "suite": "EVS-UNIT", "base_commit": "HEAD", "cases": [{"id": "c1"}]}


def outcome(provider: str | None, model: str = "m", status: str = "passed") -> dict:
    selection = {"resolved": provider is not None, "provider": provider, "model": model, "capability_class": "fast"}
    return {"id": "DLG-1", "status": status, "selection": selection, "result": {"items": []}, "errors": [], "usage": {}, "model_resolved": model}


class CallRouteTests(unittest.TestCase):
    def call(self, route_spec: str, answered: dict) -> dict:
        with mock.patch.object(evaluation, "_builders", return_value={"unit_family": lambda case_file: ("prompt", None)}), \
             mock.patch.object(evaluation, "delegate", return_value=answered):
            return evaluation.call_route(evaluation.parse_route(route_spec), CASE_FILE, Path(tempfile.gettempdir()))

    def test_honoured_override_passes_through(self) -> None:
        self.assertEqual(self.call("local:m@fast", outcome("local"))["status"], "passed")
        self.assertEqual(self.call("local@fast", outcome("local", model="other"))["status"], "passed")  # no model pinned

    def test_other_provider_answering_fails_the_sample(self) -> None:
        result = self.call("local:m@fast", outcome("cloud"))
        self.assertEqual((result["status"], result["result"]), ("override_not_honoured", None))
        self.assertIn("local:m", result["errors"][0])
        self.assertIn("cloud:m", result["errors"][0])

    def test_other_model_answering_fails_the_sample(self) -> None:
        self.assertEqual(self.call("local:m@fast", outcome("local", model="m2"))["status"], "override_not_honoured")

    def test_unresolved_or_already_failed_outcomes_are_left_alone(self) -> None:
        failed = outcome(None, status="unroutable")
        self.assertEqual(self.call("local:m@fast", failed)["status"], "unroutable")


class ScoreSampleTests(unittest.TestCase):
    def test_no_capability_observation_for_a_route_that_was_not_honoured(self) -> None:
        bad = {**outcome("cloud"), "status": "override_not_honoured", "result": None, "errors": ["override_not_honoured: ..."]}
        with mock.patch.object(evaluation.capability, "record_observation") as record:
            scored = evaluation.score_sample(evaluation.parse_route("local:m@fast"), bad, CASE_FILE, floor=0.9)
        record.assert_not_called()
        self.assertEqual((scored["status"], scored["accuracy"]), ("override_not_honoured", None))
        self.assertTrue(scored["failure"].startswith("override_not_honoured"))

    def test_honoured_samples_still_record_observations(self) -> None:
        with mock.patch.object(evaluation.capability, "record_observation") as record, \
             mock.patch.object(evaluation, "_scorer", return_value=lambda answer, cases: {"cases": 1, "correct": 1, "accuracy": 1.0, "wrong": []}):
            evaluation.score_sample(evaluation.parse_route("local:m@fast"), outcome("local"), CASE_FILE, floor=0.9)
        record.assert_called_once()


if __name__ == "__main__":
    unittest.main()
