import unittest

from src.agent_os.executive.brain_dump import (
    RECORD_TYPES, classify, process, record_id, resolve_project, split_segments,
)


class BrainDumpTests(unittest.TestCase):
    def test_split_and_classify(self):
        self.assertEqual(split_segments("- Remind me to call.\n2) Compare plans; maybe we could wait!"),
                         ["Remind me to call", "Compare plans", "maybe we could wait!"])
        self.assertEqual(split_segments("2.5 hours on report"), ["2.5 hours on report"])
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

    def test_classify_each_record_type(self):
        examples = {
            "Remind me to renew the license": "reminder",
            "Dentist appointment Tuesday": "appointment",
            "Follow up with the vendor": "follow_up",
            "Research standing desks": "research_request",
            "We decided to keep the old router": "decision",
            "Shipped the new form": "project_update",
            "What if we batch the invoices": "idea",
            "Clean the garage": "task",
        }
        self.assertEqual(set(examples.values()), set(RECORD_TYPES))
        for text, expected in examples.items():
            with self.subTest(text=text):
                self.assertEqual(classify(text), expected)

    def test_process_ambiguous_project_lists_candidates(self):
        result = process("Merge alpha into beta", known_projects=[{"id": "alpha"}, {"id": "beta"}])
        self.assertIsNone(result["records"][0]["project"])
        clarification = result["clarifications"][0]
        self.assertEqual(clarification["reason"], "ambiguous_project")
        self.assertEqual(clarification["candidates"], ["alpha", "beta"])

    def test_process_reuses_one_shot_project_iterable(self):
        projects = (project for project in [{"id": "alpha"}])
        result = process("Ship alpha. Review alpha", known_projects=projects)
        self.assertEqual([record["project"] for record in result["records"]], ["alpha", "alpha"])


if __name__ == "__main__":
    unittest.main()
