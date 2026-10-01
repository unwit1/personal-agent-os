"""Open-source prior-art registry: validation, lookup, staleness, discovery
queries, deterministic refresh, and continuation-prompt integration."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import continuation, prior_art  # noqa: E402

EVIDENCE = {key: "unknown" for key in prior_art.EVIDENCE_DIMENSIONS}


def entry(**extra):
    base = {"id": "PA-tenacity", "name": "Tenacity", "repository": "https://github.com/jd/tenacity", "license": "Apache-2.0", "evaluated_at": "2026-09-29",
            "capability_areas": ["retry orchestration", "exponential backoff", "jitter"], "agent_os_overlap": "none: no backoff in engine.py",
            "decision": "BORROW", "rationale": "small algorithm", "confidence": "medium", "evidence": dict(EVIDENCE), "revisit_when": ["Agent OS adds network retries"]}
    base.update(extra)
    return base


class RegistryTests(unittest.TestCase):
    def test_entry_validation(self) -> None:
        self.assertEqual(prior_art.entry_problems(entry()), [])
        self.assertTrue(any("decision" in item for item in prior_art.entry_problems(entry(decision="MAYBE"))))
        self.assertTrue(any("blended score" in item for item in prior_art.entry_problems(entry(evidence={**EVIDENCE, "score": 7}))))
        self.assertTrue(any("dimensions" in item for item in prior_art.entry_problems(entry(evidence={"quality": "x"}))))
        # Research alone never promotes a dependency.
        self.assertTrue(any("ADOPT requires" in item for item in prior_art.entry_problems(entry(decision="ADOPT"))))
        self.assertEqual(prior_art.entry_problems(entry(decision="ADOPT", links=[{"rel": "evidence_for", "ref": "EVR-0099"}])), [])

    def test_repository_registry_is_valid(self) -> None:
        self.assertEqual(prior_art.validate(), [])

    def test_lookup_and_queries_are_task_specific(self) -> None:
        registry = {"entries": [entry(), entry(id="PA-optuna", name="Optuna", capability_areas=["hyperparameter search"], rationale="tuning")]}
        matches = prior_art.lookup("add bounded exponential backoff with jitter to provider retries", registry)
        self.assertEqual(matches[0]["id"], "PA-tenacity")
        queries = prior_art.queries("durable checkpoint resume for agent runs", registry)
        self.assertTrue(all("best" not in query for query in queries))
        self.assertTrue(any("durable" in query and "checkpoint" in query for query in queries))

    def test_openrouter_free_routing_prior_art_is_recorded(self) -> None:
        # IMP-0015 FreeComputeBroker: the design consulted this lookup.
        matches = prior_art.lookup("OpenRouter free model routing")
        self.assertEqual(matches[0]["id"], "PA-openrouter-api")
        recorded = {item["id"]: item for item in prior_art.load()["entries"]}["PA-openrouter-api"]
        self.assertNotEqual(recorded["decision"], "ADOPT")
        self.assertIn({"rel": "relates_to", "ref": "IMP-0015"}, recorded["links"])

    def test_staleness_by_decision_window(self) -> None:
        registry = {"entries": [entry(decision="INVESTIGATE", evaluated_at="2026-08-01"), entry(id="PA-b", decision="BORROW", evaluated_at="2026-08-01"), entry(id="PA-c", revisit_by="2026-09-01")]}
        due = {item["id"] for item in prior_art.stale(registry, today=date(2026, 9, 29))}
        self.assertEqual(due, {"PA-tenacity", "PA-c"})

    def test_refresh_records_changes_deterministically(self) -> None:
        responses = {
            "https://api.github.com/repos/jd/tenacity": {"license": {"spdx_id": "Apache-2.0"}, "stargazers_count": 7000, "pushed_at": "2026-09-01T00:00:00Z", "archived": False, "language": "Python"},
            "https://api.github.com/repos/jd/tenacity/releases/latest": {"tag_name": "9.1.2", "published_at": "2026-08-01T00:00:00Z"},
        }

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def opener(request, timeout=20):
            return Response(json.dumps(responses[request.full_url]).encode())

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            path.write_text(json.dumps({"entries": [entry()]}), encoding="utf-8")
            changes = prior_art.refresh([], write=True, path=path, opener=opener)
            self.assertEqual(changes[0]["changed"]["latest_release"], [None, "9.1.2"])
            saved = json.loads(path.read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual((saved["activity"]["pushed_at"], saved["license_spdx"]), ("2026-09-01", "Apache-2.0"))


class ContinuationTests(unittest.TestCase):
    STATUS = {"schema": "s", "phase": "p", "active_objective": "o", "completed": [], "blockers": [], "recent_decisions": [],
              "next_action": {"summary": "Implement X", "worker_class": "balanced", "effort": "medium", "context_refs": [], "stop_conditions": ["done"]}}

    def test_prior_art_line_only_when_relevant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plain = continuation.build(self.STATUS, directory=Path(tmp))["next_prompt"]
            self.assertNotIn("prior-art", plain)
            status = json.loads(json.dumps(self.STATUS))
            status["next_action"]["prior_art"] = "durable checkpoint resume"
            with_prior = continuation.build(status, directory=Path(tmp))["next_prompt"]
            self.assertIn('prior-art lookup \\"durable checkpoint resume\\"'.replace('\\"', '"'), with_prior)


if __name__ == "__main__":
    unittest.main()
