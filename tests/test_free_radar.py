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
        # Only free models should be added
        self.assertEqual(len(result["new"]), 2)  # acme/alpha:free and acme/beta:free
        self.assertEqual(set(result["new"]), {"acme/alpha:free", "acme/beta:free"})

        catalog = self._catalog()
        for model_id in result["new"]:
            model = catalog["models"][model_id]
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
        v1_snapshot["fetched_at"] = "2026-10-01T10:00:00Z"

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        catalog1 = self._catalog()

        # acme/beta:free should be in v1 catalog
        self.assertIn("acme/beta:free", catalog1["models"])
        beta_first_seen = catalog1["models"]["acme/beta:free"]["last_seen"]

        # Load v2 which removes acme/beta:free
        v2_payload = load_fixture("openrouter-models-v2.json")
        v2_snapshot = fake_discover(v2_payload)
        v2_snapshot["fetched_at"] = "2026-10-02T10:00:00Z"

        result2 = radar.merge_free_catalog(v2_snapshot, home=self.home)
        catalog2 = self._catalog()

        # acme/beta:free should still exist but be marked unavailable
        self.assertIn("acme/beta:free", catalog2["models"])
        beta_model = catalog2["models"]["acme/beta:free"]
        self.assertEqual(beta_model.get("available"), False)
        # last_seen should be unchanged from v1 (not overwritten with v2's fetched_at)
        self.assertEqual(beta_model["last_seen"], beta_first_seen)
        # unavailable_since should be set to v2's fetched_at
        self.assertEqual(beta_model.get("unavailable_since"), "2026-10-02T10:00:00Z")

    def test_merge_queues_new_models_for_eval(self) -> None:
        """Newly added free models are queued to eval-queue.jsonl."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        queue1 = self._queue()

        # Should queue exactly 2 models (the new ones)
        self.assertEqual(len(queue1), 2)
        self.assertEqual(len(queue1), len(result1["new"]))
        self.assertEqual(set(e["model_id"] for e in queue1), {"acme/alpha:free", "acme/beta:free"})

        # Check queue entry structure and content
        for entry in queue1:
            self.assertIn("at", entry)
            self.assertIn("model_id", entry)
            self.assertIn("revision", entry)
            self.assertIn("reason", entry)
            self.assertIn("modalities", entry)
            self.assertIn("suggested_suites", entry)
            self.assertEqual(entry["status"], "queued")
            # Reason should mention free tier and context_length
            self.assertIn("free", entry["reason"].lower())
            self.assertIn("context_length", entry["reason"].lower())

    def test_merge_suggests_suites_by_modality(self) -> None:
        """Queue entries have suggested_suites based on modalities."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        queue1 = self._queue()

        # v1 has text modality models (acme/alpha:free, acme/beta:free both have text)
        text_entries = [e for e in queue1 if "text" in e.get("modalities", [])]
        self.assertGreater(len(text_entries), 0)
        for entry in text_entries:
            # Text modality should suggest EVS-CAPABILITY-CLASSIFICATION and EVS-CONTEXT
            self.assertEqual(set(entry["suggested_suites"]), {"EVS-CAPABILITY-CLASSIFICATION", "EVS-CONTEXT"})

    def test_merge_no_duplicates_in_queue(self) -> None:
        """Re-merging doesn't queue previously queued models again."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        queue1 = self._queue()
        initial_count = len(queue1)
        # v1 should queue 2 models (acme/alpha:free, acme/beta:free)
        self.assertEqual(initial_count, 2)
        queued_ids_v1 = {e["model_id"] for e in queue1}

        # Re-merge (treating as cache hit with same models)
        result2 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        queue2 = self._queue()

        # Queue should not have duplicates; new entries only added if models are new
        self.assertEqual(len(queue2), initial_count)
        self.assertEqual(len(result2["new"]), 0)
        # Queue entries should be identical
        queued_ids_v2 = {e["model_id"] for e in queue2}
        self.assertEqual(queued_ids_v1, queued_ids_v2)

    def test_merge_tracks_added_and_removed_between_versions(self) -> None:
        """Merge correctly identifies new, persisting, and removed models."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        self.assertEqual(set(result1["new"]), {"acme/alpha:free", "acme/beta:free"})
        queue1 = self._queue()
        self.assertEqual(set(e["model_id"] for e in queue1), {"acme/alpha:free", "acme/beta:free"})

        catalog1 = self._catalog()
        models_v1 = set(catalog1["models"].keys())

        v2_payload = load_fixture("openrouter-models-v2.json")
        v2_snapshot = fake_discover(v2_payload)

        result2 = radar.merge_free_catalog(v2_snapshot, home=self.home)
        # Only epsilon is new in v2
        self.assertEqual(set(result2["new"]), {"acme/epsilon:free"})
        queue2 = self._queue()
        # Queue should now have entries for alpha, beta (from v1) and epsilon (new in v2)
        queue2_ids = {e["model_id"] for e in queue2}
        self.assertEqual(queue2_ids, {"acme/alpha:free", "acme/beta:free", "acme/epsilon:free"})

        catalog2 = self._catalog()

        # acme/alpha:free should persist in both v1 and v2
        self.assertIn("acme/alpha:free", catalog1["models"])
        self.assertIn("acme/alpha:free", catalog2["models"])
        self.assertNotEqual(catalog2["models"]["acme/alpha:free"].get("available"), False)

        # acme/beta:free removed (in v1 but not v2) - should be marked unavailable
        self.assertIn("acme/beta:free", catalog1["models"])
        self.assertIn("acme/beta:free", catalog2["models"])
        self.assertEqual(catalog2["models"]["acme/beta:free"].get("available"), False)

        # acme/epsilon:free added (in v2 but not v1)
        self.assertNotIn("acme/epsilon:free", catalog1["models"])
        self.assertIn("acme/epsilon:free", catalog2["models"])
        self.assertNotEqual(catalog2["models"]["acme/epsilon:free"].get("available"), False)

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

    def test_merge_rejects_empty_snapshot(self) -> None:
        """Empty or missing models list in snapshot returns error without changes."""
        # Empty models list
        snapshot = {
            "schema_version": "agent-os/free-catalog-snapshot/v1",
            "provider": "openrouter",
            "catalog_version": "test",
            "fetched_at": "2026-10-01T00:00:00Z",
            "models": [],
        }

        result = radar.merge_free_catalog(snapshot, home=self.home)
        self.assertEqual(len(result["new"]), 0)
        self.assertEqual(result["models_seen"], 0)
        self.assertGreater(len(result["errors"]), 0)

        # Missing models key
        snapshot_no_models = {
            "schema_version": "agent-os/free-catalog-snapshot/v1",
            "provider": "openrouter",
            "catalog_version": "test",
            "fetched_at": "2026-10-01T00:00:00Z",
        }

        result2 = radar.merge_free_catalog(snapshot_no_models, home=self.home)
        self.assertEqual(len(result2["new"]), 0)
        self.assertEqual(result2["models_seen"], 0)
        self.assertGreater(len(result2["errors"]), 0)

    def test_merge_model_reappearance(self) -> None:
        """When a removed model reappears in a later snapshot, it's marked available again."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)
        v1_snapshot["fetched_at"] = "2026-10-01T10:00:00Z"

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        catalog1 = self._catalog()

        # v1 has acme/beta:free, get its timestamps
        beta_model_v1 = catalog1["models"]["acme/beta:free"]
        beta_first_seen = beta_model_v1["first_seen"]

        # Remove it in v2
        v2_payload = load_fixture("openrouter-models-v2.json")
        v2_snapshot = fake_discover(v2_payload)
        v2_snapshot["fetched_at"] = "2026-10-02T10:00:00Z"

        result2 = radar.merge_free_catalog(v2_snapshot, home=self.home)
        catalog2 = self._catalog()
        self.assertEqual(catalog2["models"]["acme/beta:free"].get("available"), False)

        # Re-add it back (simulating it appearing in v3)
        v1_snapshot["fetched_at"] = "2026-10-03T10:00:00Z"
        result3 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        catalog3 = self._catalog()

        beta_model_v3 = catalog3["models"]["acme/beta:free"]
        # first_seen should remain the original timestamp
        self.assertEqual(beta_model_v3["first_seen"], beta_first_seen)
        # available should be set to True (implicitly, no available=False)
        self.assertNotEqual(beta_model_v3.get("available"), False)
        # last_seen should be updated to the latest fetch
        self.assertEqual(beta_model_v3["last_seen"], "2026-10-03T10:00:00Z")

    def test_merge_skips_models_from_other_sources(self) -> None:
        """Free models don't overwrite models from other sources like HF scan."""
        # First, simulate adding a model via HF scan (source=huggingface_hub)
        hf_catalog = {
            "schema": "personal-agent/model-catalog/v1",
            "models": {
                "shared/model": {
                    "model_id": "shared/model",
                    "revision": "abc123",
                    "pipeline": "text-generation",
                    "license": "mit",
                    "modalities": ["text", "code"],
                    "provenance": {
                        "source": "huggingface_hub",
                        "url": "https://huggingface.co/shared/model",
                        "scan": "test-scan",
                        "fetched_at": "2026-10-01T00:00:00Z"
                    }
                }
            }
        }
        catalog_path = radar.catalog_path(self.home)
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(hf_catalog), encoding="utf-8")

        # Now try to merge a free catalog with a model_id that conflicts
        snapshot = {
            "schema_version": "agent-os/free-catalog-snapshot/v1",
            "provider": "openrouter",
            "catalog_version": "test",
            "fetched_at": "2026-10-02T00:00:00Z",
            "models": [
                {
                    "slug": "shared/model",  # Same model_id as HF model
                    "canonical_slug": "shared/model-free",
                    "revision": "free-rev",
                    "context_length": 4096,
                    "modalities": {"input": ["text"], "output": ["text"]},
                    "supports_tools": False,
                    "supports_structured_output": False,
                    "pricing": {},
                }
            ],
        }

        result = radar.merge_free_catalog(snapshot, home=self.home)
        catalog = self._catalog()

        # The HF version should be preserved, not overwritten
        model = catalog["models"]["shared/model"]
        self.assertEqual(model["provenance"]["source"], "huggingface_hub")
        self.assertEqual(model["revision"], "abc123")
        # Free model should not have been added
        self.assertEqual(len(result["new"]), 0)

    def test_merge_preserves_enriched_fields_on_re_merge(self) -> None:
        """Capabilities and other enriched fields added post-merge survive re-merge."""
        v1_payload = load_fixture("openrouter-models-v1.json")
        v1_snapshot = fake_discover(v1_payload)

        result1 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        catalog1 = self._catalog()

        model_id = result1["new"][0] if result1["new"] else None
        self.assertIsNotNone(model_id)

        # Simulate eval enrichment: add capabilities to the model
        model_before = catalog1["models"][model_id]
        self.assertEqual(model_before["capabilities"], [])
        model_before["capabilities"] = ["reasoning", "long_context"]
        model_before["eval_status"] = "in_progress"

        # Write the enriched catalog back
        catalog_path = radar.catalog_path(self.home)
        catalog1["updated_at"] = "2026-10-01T15:00:00Z"
        catalog_path.write_text(json.dumps(catalog1), encoding="utf-8")

        # Re-merge with new timestamp
        v1_snapshot["fetched_at"] = "2026-10-02T00:00:00Z"
        result2 = radar.merge_free_catalog(v1_snapshot, home=self.home)
        catalog2 = self._catalog()

        # Enriched fields should be preserved
        model_after = catalog2["models"][model_id]
        self.assertEqual(model_after["capabilities"], ["reasoning", "long_context"])
        self.assertEqual(model_after["eval_status"], "in_progress")
        # But metadata should be updated
        self.assertEqual(model_after["last_seen"], "2026-10-02T00:00:00Z")
        # Model should not be marked as new on re-merge
        self.assertEqual(len(result2["new"]), 0)


if __name__ == "__main__":
    unittest.main()
