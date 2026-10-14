"""The staged model-services research is present and well-formed."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "projects" / "personal-agent-os" / "research" / "model-services"


class ResearchFilesTest(unittest.TestCase):
    def test_docs_present(self):
        for name in ("SCHEMA.md", "VERIFICATION.md", "IMPLEMENTATION-SPEC.md"):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_spec_has_no_absolute_inbox_paths(self):
        self.assertNotIn("research-inbox", (ROOT / "IMPLEMENTATION-SPEC.md").read_text(encoding="utf-8"))

    def test_raw_batches_parse(self):
        batches = {}
        for path in sorted((ROOT / "raw").glob("batch-*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("batch", data, path.name)
            self.assertIsInstance(data.get("records"), list, path.name)
            batches[path.stem.split("-", 1)[1]] = len(data["records"])
        for batch in "ABCD":
            self.assertIn(batch, batches)


if __name__ == "__main__":
    unittest.main()
