"""IMP-0015: capability evidence keyed by exact model revision when known."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import capability  # noqa: E402
from agent_os.orchestrator.model_profile import endpoint_entry  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry, select  # noqa: E402

BASE = {"task_family": "fam", "role": "analyst", "provider": "local-a", "model_resolved": "org/m", "effort": "low", "toolset": "read_only",
        "status": "passed", "validator_passed": True, "accuracy": 1.0}


class RevisionKeyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.registry = ProviderRegistry(providers=[endpoint_entry("local-a", base_url="http://127.0.0.1:8000", model="org/m", classes=["fast"], revision="abcdef1234567890")])

    def test_records_fill_revision_from_the_registry_profile(self) -> None:
        capability.record_observation(dict(BASE), home=self.home, registry=self.registry)
        capability.record_observation({**BASE, "provider": "unknown"}, home=self.home, registry=self.registry)
        rows = capability.read_observations(self.home)
        self.assertEqual([row.get("model_revision") for row in rows], ["abcdef1234567890", None])

    def test_explicit_revision_is_kept(self) -> None:
        capability.record_observation({**BASE, "model_revision": "fedcba"}, home=self.home, registry=self.registry)
        self.assertEqual(capability.read_observations(self.home)[0]["model_revision"], "fedcba")

    def test_revisions_aggregate_separately_and_unrevised_ids_are_unchanged(self) -> None:
        legacy = capability.summarize([dict(BASE)])[0]
        self.assertEqual(legacy["key"]["model_resolved"], "org/m")
        self.assertEqual(legacy["id"], capability.cap_id({**BASE}))
        records = capability.summarize([{**BASE, "model_revision": "aaaaaaaaaaaaaaaa"}, {**BASE, "model_revision": "bbbbbbbbbbbbbbbb"}, dict(BASE)])
        self.assertEqual(sorted(record["key"]["model_resolved"] for record in records), ["org/m", "org/m@aaaaaaaaaaaa", "org/m@bbbbbbbbbbbb"])
        self.assertEqual(len({record["id"] for record in records}), 3)

    def test_selection_and_registry_carry_the_revision(self) -> None:
        choice = select(self.registry, capability_class="fast", effort="low", role="inline")
        self.assertEqual(choice["profile"]["revision"], "abcdef1234567890")
        self.assertEqual(self.registry.get("local-a")["profile"]["revision"], "abcdef1234567890")


if __name__ == "__main__":
    unittest.main()
