from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "rtec-hr-process-model"
    / "audits"
    / "filesystem-reconciliation"
    / "inventory.py"
)
SPEC = importlib.util.spec_from_file_location("rtec_hr_filesystem_inventory", MODULE_PATH)
assert SPEC and SPEC.loader
inventory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = inventory
SPEC.loader.exec_module(inventory)


class RtecHrFilesystemInventoryTests(unittest.TestCase):
    def test_server_drive_and_applicant_roots_are_excluded(self) -> None:
        self.assertFalse(inventory.safe_root(Path("R:/")))
        self.assertTrue(inventory.blocked_directory(Path("R:/HR/Shared")))
        self.assertTrue(inventory.blocked_directory(Path("C:/Work/Job Applicant Dashboard")))
        self.assertTrue(inventory.blocked_directory(Path("C:/Work/_Pending_New_Hires")))

    def test_profile_name_does_not_make_every_file_hr_relevant(self) -> None:
        root = Path("C:/Users/HR.RTEC/Desktop")
        likely, route = inventory.relevance(root / "personal-notes.pdf", root)
        self.assertFalse(likely)
        self.assertEqual(route, "unclassified_work_document")
        self.assertTrue(inventory.relevance(root / "benefits" / "plan-guide.pdf", root)[0])

    def test_discovery_resumes_after_a_bounded_file_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "HR"
            root.mkdir()
            for name in ("a-policy.pdf", "b-policy.pdf", "c-policy.pdf"):
                (root / name).write_bytes(name.encode("ascii"))
            db = inventory.connect(Path(tmp) / "audit.sqlite3")
            inventory.add_roots(db, [root])

            seen = 0
            while db.execute("SELECT COUNT(*) FROM directories WHERE status='queued'").fetchone()[0]:
                inventory.discover_batch(db, max_dirs=1, max_files=1)
                seen = db.execute("SELECT COUNT(*) FROM files").fetchone()[0]

            self.assertEqual(seen, 3)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM directories WHERE status='done'").fetchone()[0], 1)
            db.close()


if __name__ == "__main__":
    unittest.main()
