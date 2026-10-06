import unittest

from src.agent_os.executive.brain_dump import (
    RECORD_TYPES, classify, process, record_id, resolve_project, split_segments,
)


class BrainDumpTests(unittest.TestCase):
    def test_split_and_classify(self):
        self.assertEqual(split_segments("- Remind me to call.\n2) Compare plans; maybe we could wait!"),
                         ["Remind me to call", "Compare plans", "maybe we could wait!"])
        self.assertEqual(classify("Remind me about the doctor"), "reminder")
        self.assertEqual(classify("Call with Pat at 3pm"), "appointment")
        self.assertEqual(set(RECORD_TYPES), {"task", "idea", "reminder", "appointment", "decision", "project_update", "research_request", "follow_up"})

    def test_project_resolution(self):
        projects = [{"id": "alpha", "aliases": ["Apollo"]}, {"id": "beta"}]
        self.assertEqual(resolve_project("Ship Apollo", projects), ("alpha", None))
        self.assertEqual(resolve_project("alpha and beta", projects), (None, "ambiguous_project"))
        self.assertEqual(resolve_project("work on @missing", projects), (None, "unknown_reference"))
        self.assertEqual(resolve_project("alphabet", projects), (None, None))

    def test_process_duplicates_and_clarifications(self):
        result = process("Ship alpha. Ship alpha. Do @unknown", known_projects=[{"id": "alpha"}])
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["duplicates"][0]["reason"], "repeated_in_dump")
        self.assertEqual(result["clarifications"][0]["reason"], "unknown_reference")
        self.assertEqual(result["records"][0]["confidence"], 0.9)
        existing = record_id("task", "Ship alpha")
        self.assertEqual(process("Ship alpha", known_projects=[{"id": "alpha"}], existing_ids=[existing])["duplicates"][0]["reason"], "already_captured")


if __name__ == "__main__":
    unittest.main()
