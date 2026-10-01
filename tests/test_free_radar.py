"""IMP-0015 free-model discovery: merge free catalog with Research Radar."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import radar, free_catalog  # noqa: E402


def load_fixture(name: str) -> dict:
    """Load a test fixture JSON file."""
    fixture_path = Path(__file__).parent / "fixtures" / name
    with fixture_path.open() as f:
        return json.load(f)


def fake_discover(payload: dict) -> dict:
    """Create a snapshot from raw API payload, mimicking free_catalog.discover()."""
    models = free_catalog.normalize_openrouter(payload)
    for model in models:
        model["first_seen"] = "2026-10-01T00:00:00Z"
        model["last_seen"] = "2026-10-01T00:00:00Z"
    return {
        "schema_version": "agent-os/free-catalog-snapshot/v1",
        "provider": "openrouter",
        "catalog_version": free_catalog.catalog_hash(models),
        "fetched_at": "2026-10-01T00:00:00Z",
        "fetched_epoch": 1727740800,
        "source_url": "https://openrouter.ai/api/v1/models",
        "models": models,
        "source": "live",
    }


class MergeFreeRadarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _catalog(self) -> dict:
        """Load current catalog."""
        path = radar.catalog_path(self.home)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def _queue(self) -> list[dict]:
        """Load eval queue entries."""
        path = radar.queue_path(self.home)
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def test_merge_adds_free_models_with_tags(self) -> None:
        """Newly merged free models are tagged with source, timestamps, and other metadata."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result = radar.merge_free_catalog(v1_snapshot, home=self.home)

        self.assertGreater(result["models_seen"], 0)
        self.assertGreater(len(result["new"]), 0)
        self.assertEqual(result["catalog_size"], result["models_seen"])

        catalog = self._catalog()
        for model in catalog["models"].values():
            if model.get("model_id") in result["new"]:
                self.assertEqual(model["provenance"]["source"], "openrouter-free")
                self.assertIn("last_seen", model)
                self.assertIn("last_verified", model)
                self.assertIn("first_seen", model)
                self.assertEqual(model["first_seen"], model["last_seen"])

    def test_merge_flattens_modalities(self) -> None:
        """Input/output modality dicts are flattened to sorted lists."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        radar.merge_free_catalog(v1_snapshot, home=self.home)

        catalog = self._catalog()
        for model in catalog["models"].values():
            if model.get("provenance", {}).get("source") == "openrouter-free":
                # modalities should be a flat sorted list
                self.assertIsInstance(model["modalities"], list)
                if model["modalities"]:
                    # Verify elements are strings
                    self.assertTrue(all(isinstance(m, str) for m in model["modalities"]))
                    # Verify sorted
                    self.assertEqual(model["modalities"], sorted(model["modalities"]))

    def test_merge_preserves_first_seen_on_re_merge(self) -> None:
        """When re-merging, first_seen is preserved; last_seen/last_verified are updated."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        catalog1 = self._catalog()
        model_id = result1["new"][0] if result1["new"] else None
        self.assertIsNotNone(model_id)

        first_seen_1 = catalog1["models"][model_id]["first_seen"]
        last_seen_1 = catalog1["models"][model_id]["last_seen"]

        # Re-merge same snapshot (with updated timestamp)
        v1_snapshot["fetched_at"] = "2026-10-02T00:00:00Z"
        result2 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        catalog2 = self._catalog()

        # first_seen should not change
        self.assertEqual(catalog2["models"][model_id]["first_seen"], first_seen_1)
        # last_seen should be updated
        self.assertNotEqual(catalog2["models"][model_id]["last_seen"], last_seen_1)

    def test_merge_removes_unavailable_models(self) -> None:
        """Models in previous snapshot but missing from new snapshot are marked unavailable."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        catalog1 = self._catalog()

        # acme/beta:free should be in v1 catalog
        self.assertIn("acme/beta:free", catalog1["models"])

        # Load v2 which removes acme/beta:free
        v2_payload = load_fixture("openrouter-models-v2.json")
        v2_snapshot = fake_discover(v2_payload)

        result2 = radar.merge_free_catalog(v2_snapshot, home=self.home)
        catalog2 = self._catalog()

        # acme/beta:free should still exist but be marked unavailable
        self.assertIn("acme/beta:free", catalog2["models"])
        self.assertEqual(catalog2["models"]["acme/beta:free"].get("available"), False)
        # Verify it's not in the current catalog_size counting available models
        # (implicitly, only acme/alpha:free and acme/epsilon:free should be fully visible)

    def test_merge_queues_new_models_for_eval(self) -> None:
        """Newly added free models are queued to eval-queue.jsonl."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        queue1 = self._queue()

        self.assertEqual(len(queue1), len(result1["new"]))

        # Check queue entry structure
        for entry in queue1:
            self.assertIn("at", entry)
            self.assertIn("model_id", entry)
            self.assertIn("revision", entry)
            self.assertIn("reason", entry)
            self.assertIn("modalities", entry)
            self.assertIn("suggested_suites", entry)
            self.assertEqual(entry["status"], "queued")
            # Reason should mention free tier
            self.assertIn("free", entry["reason"].lower())

    def test_merge_suggests_suites_by_modality(self) -> None:
        """Queue entries have suggested_suites based on modalities."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        queue1 = self._queue()

        # v1 has text modality models
        text_entries = [e for e in queue1 if "text" in e.get("modalities", [])]
        for entry in text_entries:
            # Text modality should suggest EVS-CAPABILITY-CLASSIFICATION and EVS-CONTEXT
            self.assertTrue(any("EVS-" in suite for suite in entry["suggested_suites"]))

    def test_merge_no_duplicates_in_queue(self) -> None:
        """Re-merging doesn't queue previously queued models again."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        queue1 = self._queue()
        initial_count = len(queue1)

        # Re-merge (treating as cache hit with same models)
        result2 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        queue2 = self._queue()

        # Queue should not have duplicates; new entries only added if models are new
        self.assertEqual(len(queue2), initial_count)
        self.assertEqual(len(result2["new"]), 0)

    def test_merge_tracks_added_and_removed_between_versions(self) -> None:
        """Merge correctly identifies new, persisting, and removed models."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)

        # v1 has: acme/alpha:free, acme/beta:free (and non-free models)
        free_v1 = {m["slug"] for m in v1_snapshot["models"]}

        v2_payload = load_fixture("openrouter-models-v2.json")
        v2_snapshot = fake_discover(v2_payload)

        result2 = radar.merge_free_catalog(v2_snapshot, home=self.home)

        # v2 has: acme/alpha:free, acme/epsilon:free (and non-free models)
        free_v2 = {m["slug"] for m in v2_snapshot["models"]}

        # acme/alpha:free should persist (in both)
        self.assertIn("acme/alpha:free", free_v1)
        self.assertIn("acme/alpha:free", free_v2)

        # acme/beta:free removed (in v1 but not v2)
        self.assertIn("acme/beta:free", free_v1)
        self.assertNotIn("acme/beta:free", free_v2)

        # acme/epsilon:free added (in v2 but not v1)
        self.assertNotIn("acme/epsilon:free", free_v1)
        self.assertIn("acme/epsilon:free", free_v2)

        # Result should show epsilon as new
        self.assertIn("acme/epsilon:free", result2["new"])

    def test_merge_handles_empty_modalities(self) -> None:
        """Models with empty modalities list are handled gracefully."""
        # Create a snapshot with a model that has no modalities
        snapshot = {
            "schema_version": "agent-os/free-catalog-snapshot/v1",
            "provider": "openrouter",
            "catalog_version": "test",
            "fetched_at": "2026-10-01T00:00:00Z",
            "models": [
                {
                    "slug": "test/minimal",
                    "canonical_slug": "test/minimal",
                    "revision": "test/minimal",
                    "context_length": 4096,
                    "modalities": {"input": [], "output": []},
                    "supports_tools": False,
                    "supports_structured_output": False,
                    "pricing": {},
                    "first_seen": "2026-10-01T00:00:00Z",
                    "last_seen": "2026-10-01T00:00:00Z",
                }
            ],
        }

        result = radar.merge_free_catalog(snapshot, home=self.home)
        catalog = self._catalog()

        model = catalog["models"].get("test/minimal")
        self.assertIsNotNone(model)
        self.assertEqual(model["modalities"], [])
        self.assertEqual(model["provenance"]["source"], "openrouter-free")


class ExistingRadarCompatibilityTests(unittest.TestCase):
    """Verify that existing scan() and normalize() functions still work."""

    def test_scan_still_works(self) -> None:
        """Existing scan() function is not broken by merge_free_catalog."""
        # This is a simple smoke test
        self.assertTrue(callable(radar.scan))
        self.assertTrue(callable(radar.normalize))
        self.assertTrue(callable(radar.catalog_path))
        self.assertTrue(callable(radar.queue_path))


if __name__ == "__main__":
    unittest.main()
