from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.forms import load_form_registry_incremental


class IncrementalFormRegistryImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.registry = root / "registry.json"
        self.ledger = root / "ingestion.json"
        self._write("fixture form registry")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write(self, description: str) -> None:
        self.registry.write_text(
            json.dumps(
                {
                    "schema": "personal-agent/form-registry/v1",
                    "version": 1,
                    "forms": [{"id": "fixture-form", "description": description}],
                }
            ),
            encoding="utf-8",
        )

    def _run(self, **kwargs: object) -> dict[str, object]:
        return load_form_registry_incremental(
            self.registry,
            ledger_path=self.ledger,
            **kwargs,
        )

    def test_reimport_is_idempotent_and_ledger_is_metadata_only(self) -> None:
        first = self._run()
        second = self._run()

        self.assertEqual(first["stats"]["queued"], 1)
        self.assertEqual(second["stats"]["skipped"], 1)
        self.assertEqual(first["registry"], second["registry"])
        ledger_blob = self.ledger.read_text(encoding="utf-8")
        self.assertNotIn("fixture form registry", ledger_blob)

    def test_changed_content_requeues_the_registry(self) -> None:
        self._run()
        self._write("changed fixture registry")

        result = self._run()
        self.assertEqual(result["stats"]["reprocessed"], 1)
        self.assertEqual(result["registry"]["forms"][0]["description"], "changed fixture registry")

    def test_interruption_recovers_the_processing_registry(self) -> None:
        def interrupt(path: Path) -> None:
            raise KeyboardInterrupt("fixture interruption")

        with self.assertRaises(KeyboardInterrupt):
            self._run(before_parse=interrupt)

        interrupted = json.loads(self.ledger.read_text(encoding="utf-8"))
        item = next(iter(interrupted["items"].values()))
        self.assertEqual(item["status"], "processing")
        self.assertIsNone(interrupted["checkpoint"]["cursor"])

        resumed = self._run()
        self.assertEqual(resumed["stats"]["resumed"], 1)
        self.assertEqual(resumed["checkpoint"]["cursor"], "registry.json")

    def test_checkpoint_continues_after_completed_registry(self) -> None:
        first = self._run()
        second = self._run()

        self.assertEqual(first["checkpoint"]["cursor"], "registry.json")
        self.assertGreater(second["checkpoint"]["sequence"], first["checkpoint"]["sequence"])
        self.assertEqual(second["checkpoint"]["cursor"], "registry.json")


if __name__ == "__main__":
    unittest.main()
