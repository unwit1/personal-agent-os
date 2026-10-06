import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import brain_dump
from agent_os.executive.window.brain_dump_store import BrainDumpStore
from agent_os.executive.window.providers_brain_dump import brain_dump_items
from agent_os.executive.window_queue import queue_item_from_window_item


class BrainDumpProviderTests(unittest.TestCase):
    def test_open_records_map_to_window_items_and_staged_records_are_excluded(self):
        with tempfile.TemporaryDirectory() as home:
            store = BrainDumpStore(home)
            projects = [
                {"id": "alpha", "aliases": ["Apollo"]},
                {"id": "beta", "aliases": ["Apollo"]},
                {"id": "gamma", "aliases": []},
            ]
            resolved = brain_dump.process("Finish gamma report", known_projects=projects)
            ambiguous = brain_dump.process("Call Apollo team", known_projects=projects)
            unknown = brain_dump.process("Research #foo", known_projects=projects)
            store.add(resolved, tab="work")
            store.add(ambiguous, tab="work")
            store.add(unknown, tab="work")

            staged_record = brain_dump.process("Email gamma", known_projects=projects)
            staged_id = store.add(staged_record, tab="work")[0]
            store.mark_staged(staged_id, {})

            items = brain_dump_items(store)
            by_title = {item["title"]: item for item in items}
            resolved_record = resolved["records"][0]
            ambiguous_record = ambiguous["records"][0]
            unknown_record = unknown["records"][0]

            self.assertEqual(set(by_title), {"Finish gamma report", "Call Apollo team", "Research #foo"})
            self.assertEqual(by_title["Finish gamma report"]["id"], f"brain-dump:{resolved_record['id']}")
            self.assertEqual(by_title["Finish gamma report"]["kind"], "brain_dump_record")
            self.assertEqual(by_title["Finish gamma report"]["why"], "Brain dump task for gamma")
            self.assertEqual(by_title["Finish gamma report"]["context"], {
                "record_id": resolved_record["id"], "type": "task", "project": "gamma", "candidates": [],
            })

            ambiguous_item = by_title["Call Apollo team"]
            self.assertEqual(ambiguous_item["id"], f"brain-dump:{ambiguous_record['id']}")
            self.assertEqual(ambiguous_item["kind"], "brain_dump_clarification")
            self.assertEqual(ambiguous_item["why"], "Which project? (ambiguous_project; candidates: alpha, beta)")
            self.assertEqual(ambiguous_item["context"], {
                "record_id": ambiguous_record["id"], "type": "follow_up", "project": None,
                "candidates": ["alpha", "beta"],
            })

            unknown_item = by_title["Research #foo"]
            self.assertEqual(unknown_item["id"], f"brain-dump:{unknown_record['id']}")
            self.assertEqual(unknown_item["kind"], "brain_dump_clarification")
            self.assertEqual(unknown_item["why"], "Which project? (unknown_reference)")
            self.assertEqual(unknown_item["context"], {
                "record_id": unknown_record["id"], "type": "research_request", "project": None,
                "candidates": [],
            })

            for item in items:
                queue_item_from_window_item(item, "brain_dump")


if __name__ == "__main__":
    unittest.main()
