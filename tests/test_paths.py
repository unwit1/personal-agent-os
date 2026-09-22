import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.paths import ROOT, project_collection_dir  # noqa: E402


class ProjectCollectionPathTests(unittest.TestCase):
    def test_synthetic_collection_path_uses_the_canonical_project_root(self) -> None:
        self.assertEqual(
            project_collection_dir("fixture-project", "records"),
            ROOT / "projects" / "fixture-project" / "records",
        )

    def test_collections_remain_distinct(self) -> None:
        candidates = project_collection_dir("fixture-project", "candidates")
        changes = project_collection_dir("fixture-project", "changes")
        self.assertNotEqual(candidates, changes)
        self.assertEqual(candidates.parent, changes.parent)

    def test_callers_can_preserve_a_synthetic_root_override(self) -> None:
        synthetic_root = ROOT / ".tmp" / "path-fixture"
        self.assertEqual(
            project_collection_dir("fixture-project", "records", root=synthetic_root),
            synthetic_root / "projects" / "fixture-project" / "records",
        )


if __name__ == "__main__":
    unittest.main()
