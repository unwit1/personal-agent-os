from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.ingestion import (  # noqa: E402
    IngestionLedger,
    content_fingerprint,
    empty_record_import_stats,
    processing_fingerprint,
    stable_item_id,
    stable_run_id,
    stable_stage_id,
    stable_work_id,
)


class IngestionLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "ledger.json"
        self.work_id = stable_work_id("fixture", "archive")
        self.stage_id = stable_stage_id(self.work_id, "normalize")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def ledger(self, version: str = "normalizer@1") -> IngestionLedger:
        return IngestionLedger(
            self.path,
            source="fixture",
            work_id=self.work_id,
            stage_id=self.stage_id,
            processor_version=version,
        )

    def test_identity_helpers_are_stable_and_namespaced(self) -> None:
        self.assertEqual(self.work_id, stable_work_id("fixture", "archive"))
        self.assertNotEqual(self.work_id, stable_work_id("fixture", "other"))
        self.assertEqual(stable_item_id("fixture", "a"), stable_item_id("fixture", "a"))
        self.assertNotEqual(stable_item_id("fixture", "a"), stable_item_id("other", "a"))
        self.assertEqual(stable_run_id(self.work_id, "normalize"), stable_run_id(self.work_id, "normalize"))

    def test_fingerprints_are_deterministic_without_retaining_content(self) -> None:
        content_hash = content_fingerprint("private source text")
        self.assertEqual(content_hash, content_fingerprint("private source text"))
        self.assertNotEqual(content_hash, content_fingerprint("changed"))
        self.assertNotEqual(processing_fingerprint(content_hash, "v1"), processing_fingerprint(content_hash, "v2"))
        self.ledger().enqueue("message-1", content="private source text")
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        serialized = json.dumps(raw)
        self.assertNotIn("private source text", serialized)

    def test_record_import_stats_are_fresh_and_have_the_shared_shape(self) -> None:
        first = empty_record_import_stats()
        first["queued"] = 1
        second = empty_record_import_stats()
        self.assertEqual(
            set(second), {"checked", "queued", "reprocessed", "resumed", "skipped", "errors"}
        )
        self.assertEqual(second["queued"], 0)

    def test_duplicate_enqueue_is_a_no_op(self) -> None:
        ledger = self.ledger()
        first = ledger.enqueue("message-1", content="same")
        duplicate = ledger.enqueue("message-1", content="same")
        self.assertEqual(first["action"], "queued")
        self.assertEqual(duplicate["action"], "duplicate")
        self.assertEqual(ledger.status()["counts"]["queued"], 1)

    def test_changed_content_or_processor_version_requeues_same_item(self) -> None:
        ledger = self.ledger()
        item_id = ledger.enqueue("message-1", content="v1")["item_id"]
        ledger.claim()
        ledger.complete(item_id, ["artifact-v1"])
        changed = ledger.enqueue("message-1", content="v2")
        self.assertEqual(changed["action"], "requeued")
        self.assertEqual(ledger.get(item_id)["revision"], 2)
        self.assertEqual(ledger.get(item_id)["output_refs"], [])

        newer = IngestionLedger(self.path, source="fixture", work_id=self.work_id, stage_id=self.stage_id, processor_version="normalizer@2")
        changed_version = newer.enqueue("message-1", content="v2")
        self.assertEqual(changed_version["action"], "requeued")

    def test_interrupted_processing_is_recovered_from_disk(self) -> None:
        ledger = self.ledger()
        item_id = ledger.enqueue("message-1", content="same")["item_id"]
        self.assertEqual(ledger.claim()[0]["status"], "processing")

        resumed = self.ledger()
        self.assertEqual(resumed.get(item_id)["status"], "queued")
        claimed = resumed.claim()[0]
        self.assertEqual(claimed["item_id"], item_id)
        self.assertEqual(resumed.complete(item_id)["status"], "processed")

    def test_completion_and_failure_are_idempotent_or_explicit(self) -> None:
        ledger = self.ledger()
        first_id = ledger.enqueue("first", content="one")["item_id"]
        second_id = ledger.enqueue("second", content="two")["item_id"]
        ledger.claim(limit=2)
        completed = ledger.complete(first_id, ["out", "out"])
        self.assertEqual(completed["output_refs"], ["out"])
        self.assertEqual(ledger.complete(first_id)["status"], "processed")
        ledger.fail(second_id, "temporary", retryable=True)
        self.assertEqual(ledger.retry_errors(), 1)
        self.assertEqual(ledger.get(second_id)["status"], "queued")

    def test_non_retryable_errors_remain_terminal(self) -> None:
        ledger = self.ledger()
        item_id = ledger.enqueue("bad", content="bad")["item_id"]
        ledger.claim()
        ledger.fail(item_id, "permanent", retryable=False)
        self.assertEqual(ledger.retry_errors(), 0)
        self.assertEqual(ledger.get(item_id)["status"], "error")

    def test_checkpoint_round_trips_and_advances(self) -> None:
        ledger = self.ledger()
        self.assertEqual(ledger.checkpoint("cursor-1", scanned=2)["sequence"], 1)
        self.assertEqual(ledger.checkpoint("cursor-2", scanned=4)["sequence"], 2)
        resumed = self.ledger()
        self.assertEqual(resumed.status()["checkpoint"]["cursor"], "cursor-2")
        self.assertEqual(resumed.status()["checkpoint"]["sequence"], 2)


class DeferredSaveAndTargetedClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "ledger.json"
        work_id = stable_work_id("fixture", "batch")
        self.ledger = IngestionLedger(self.path, source="fixture", work_id=work_id, stage_id=stable_stage_id(work_id, "s"), processor_version="p@1")

    def items_on_disk(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))["items"]

    def test_deferred_saves_write_once_at_the_end(self) -> None:
        with self.ledger.deferred_saves():
            first = self.ledger.enqueue("a", content=b"a")
            self.ledger.enqueue("b", content=b"b")
            self.assertEqual(self.items_on_disk(), {}, "nothing written inside the block")
            self.ledger.claim(1, item_ids=[first["item_id"]])
        on_disk = self.items_on_disk()
        self.assertEqual(sorted(item["status"] for item in on_disk.values()), ["processing", "queued"])

    def test_deferred_saves_flush_on_exception(self) -> None:
        with self.assertRaises(KeyboardInterrupt):
            with self.ledger.deferred_saves():
                self.ledger.enqueue("a", content=b"a")
                raise KeyboardInterrupt()
        self.assertEqual(len(self.items_on_disk()), 1)

    def test_targeted_claim_takes_only_the_named_queued_item(self) -> None:
        older = self.ledger.enqueue("old", content=b"1")
        newer = self.ledger.enqueue("new", content=b"2")
        claimed = self.ledger.claim(5, item_ids=[newer["item_id"], "missing-id"])
        self.assertEqual([item["item_id"] for item in claimed], [newer["item_id"]])
        self.assertEqual(self.ledger.get(older["item_id"])["status"], "queued")
        self.assertEqual(self.ledger.claim(1, item_ids=[newer["item_id"]]), [], "already processing")


if __name__ == "__main__":
    unittest.main()
