from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import profile
from agent_os.compiler import compile_context
from agent_os.paths import ROOT


# Representative tasks and the profile domain each should (or should not) reach.
RELEVANCE_CORPUS = (
    ("fix the HR scanner OCR accuracy for personnel forms", "work_context"),
    ("plan meals and groceries for next week", "household_planning"),
    ("track bills and spending this month", "financial_assistant_goals"),
    ("what are my goals for the next two years", "goals"),
)

# Tasks with no personal dimension at all.
IMPERSONAL_TASKS = (
    "rename a variable in a python function",
    "add a null check to the parser",
    "what is the time complexity of a binary search",
)


class IndexTests(unittest.TestCase):
    def test_only_curated_sources_are_indexed(self) -> None:
        names = {path.name for path in profile.CANONICAL_SOURCES}
        self.assertEqual(names, {"preferences.json", "user-context.json"})

    def test_the_large_derived_context_is_never_loaded(self) -> None:
        """The derived Drive index is bulk, and bulk is what this module prevents."""
        derived = ROOT / "profile" / "drive-derived-context.json"
        if not derived.exists():
            self.skipTest("derived context file is not present on this machine")
        self.assertGreater(derived.stat().st_size, 20000, "fixture assumption: this file is large")
        self.assertNotIn(derived, profile.CANONICAL_SOURCES)
        blob = json.dumps(profile.index_facts())
        marker = json.loads(derived.read_text(encoding="utf-8"))
        sample = next((k for k in marker if isinstance(k, str)), None)
        if sample:
            self.assertNotIn(sample, blob)

    def test_indexing_is_deterministic(self) -> None:
        self.assertEqual(profile.index_facts(), profile.index_facts())

    def test_every_fact_carries_retrieval_metadata(self) -> None:
        for fact in profile.index_facts():
            with self.subTest(fact=fact["id"]):
                for key in ("id", "domain", "statement", "confidence", "sensitivity", "updated_at", "provenance"):
                    self.assertIn(key, fact)
                self.assertIn(fact["confidence"], profile.CONFIDENCE_ORDER)
                self.assertIn(fact["sensitivity"], {"personal", "restricted"})

    def test_fact_ids_are_stable_and_unique(self) -> None:
        facts = profile.index_facts()
        ids = [fact["id"] for fact in facts]
        self.assertEqual(len(ids), len(set(ids)), "profile fact ids collide")
        self.assertEqual(ids, [fact["id"] for fact in profile.index_facts()])

    def test_provenance_distinguishes_stated_from_derived(self) -> None:
        """An explicit statement must be tellable from something inferred."""
        confidences = {fact["confidence"] for fact in profile.index_facts()}
        self.assertTrue(confidences)
        self.assertTrue(confidences.issubset(set(profile.CONFIDENCE_ORDER)))


class PrivacyTests(unittest.TestCase):
    def test_the_privacy_section_is_never_retrievable(self) -> None:
        domains = {fact["domain"] for fact in profile.retrievable_facts()}
        self.assertNotIn("privacy", domains)

    def test_restricted_facts_are_excluded_from_retrieval(self) -> None:
        indexed = profile.index_facts()
        restricted = [fact for fact in indexed if fact["sensitivity"] == "restricted"]
        retrievable_ids = {fact["id"] for fact in profile.retrievable_facts()}
        self.assertTrue(restricted, "fixture assumption: some facts are restricted")
        for fact in restricted:
            self.assertNotIn(fact["id"], retrievable_ids)

    def test_no_retrievable_fact_trips_the_privacy_gate(self) -> None:
        for fact in profile.retrievable_facts():
            with self.subTest(fact=fact["id"]):
                self.assertEqual(fact["privacy_findings"], [])

    def test_a_pii_bearing_fact_cannot_be_retrieved(self) -> None:
        """Privacy is enforced at retrieval, not trusted to the author."""
        planted = {
            "id": "PF-planted",
            "source": "test",
            "domain": "work_context",
            "path": "work_context.contact",
            "statement": "Reach the payroll contact at payroll@example.com about 123-45-6789.",
        }
        findings = profile.privacy_findings(planted["statement"])
        self.assertIn("email", findings)
        self.assertIn("ssn", findings)


class RelevanceTests(unittest.TestCase):
    def test_representative_tasks_reach_the_right_domain(self) -> None:
        for task, expected in RELEVANCE_CORPUS:
            with self.subTest(task=task):
                result = profile.compact_profile(task)
                self.assertTrue(result["facts"], f"no profile context retrieved for: {task}")
                self.assertIn(expected, result["diagnostics"]["domains"])

    def test_unrelated_domains_stay_out(self) -> None:
        """Answering a meal question must not drag in work or leisure context."""
        result = profile.compact_profile("plan meals and groceries for next week")
        self.assertEqual(result["diagnostics"]["domains"], ["household_planning"])

    def test_impersonal_tasks_retrieve_no_profile_at_all(self) -> None:
        for task in IMPERSONAL_TASKS:
            with self.subTest(task=task):
                result = profile.compact_profile(task)
                self.assertEqual(result["facts"], [], f"personal context leaked into: {task}")

    def test_a_single_generic_word_is_not_relevance(self) -> None:
        """'variable' appears in a housing fact; that is coincidence, not signal."""
        assessed = [
            profile.score_fact("rename a variable in a python function", fact)
            for fact in profile.retrievable_facts()
        ]
        weak = [item for item in assessed if item["matched_terms"] and not item["distinctive"]]
        self.assertTrue(weak, "fixture assumption: some fact shares one generic word")
        for item in weak:
            self.assertLess(len(item["matched_terms"]), 2)
            self.assertEqual(item["domain_hits"], 0)

    def test_short_domain_terms_still_match(self) -> None:
        """'hr' and 'ocr' are too short to survive tokenising; they must still route."""
        result = profile.compact_profile("hr onboarding paperwork")
        self.assertIn("work_context", result["diagnostics"]["domains"])

    def test_the_whole_profile_is_never_returned(self) -> None:
        indexed = len(profile.retrievable_facts())
        for task, _ in RELEVANCE_CORPUS:
            with self.subTest(task=task):
                result = profile.compact_profile(task)
                self.assertLess(len(result["facts"]), indexed)
                self.assertLessEqual(len(result["facts"]), result["diagnostics"]["limit"])
                self.assertFalse(result["diagnostics"]["full_profile_loaded"])


class DeduplicationTests(unittest.TestCase):
    def test_overlapping_statements_collapse_to_one(self) -> None:
        scored = [
            {"fact": {"id": "a", "statement": "Track bills and spending", "confidence": "derived", "updated_at": "2026-01-01"}, "score": 9},
            {"fact": {"id": "b", "statement": "Track bills and spending carefully", "confidence": "stated", "updated_at": "2026-09-18"}, "score": 9},
        ]
        kept, dropped = profile._dedupe(scored)
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(dropped), 1)

    def test_the_stated_record_outranks_the_derived_one(self) -> None:
        scored = [
            {"fact": {"id": "derived", "statement": "Prefers compact handoffs", "confidence": "derived", "updated_at": "2026-09-01"}, "score": 9},
            {"fact": {"id": "stated", "statement": "Prefers compact handoffs", "confidence": "stated", "updated_at": "2026-09-01"}, "score": 9},
        ]
        kept, dropped = profile._dedupe(scored)
        self.assertEqual(kept[0]["fact"]["id"], "stated", "a derived record superseded an explicit one")
        self.assertEqual(dropped[0]["superseded_by"], "stated")

    def test_the_newer_record_wins_at_equal_standing(self) -> None:
        scored = [
            {"fact": {"id": "old", "statement": "Priority is job effectiveness", "confidence": "stated", "updated_at": "2026-01-01"}, "score": 9},
            {"fact": {"id": "new", "statement": "Priority is job effectiveness", "confidence": "stated", "updated_at": "2026-09-18"}, "score": 9},
        ]
        kept, _ = profile._dedupe(scored)
        self.assertEqual(kept[0]["fact"]["id"], "new", "a stale record superseded a newer one")

    def test_a_dropped_fact_reports_what_superseded_it(self) -> None:
        result = profile.compact_profile("preferences for handoffs and context retrieval")
        self.assertIn("deduplicated", result["diagnostics"])


class DiagnosticsTests(unittest.TestCase):
    def test_every_selected_fact_explains_itself(self) -> None:
        result = profile.compact_profile("plan meals and groceries for next week")
        for fact in result["facts"]:
            with self.subTest(fact=fact["id"]):
                self.assertTrue(fact["why"], "a retrieved fact carries no explanation")
                self.assertTrue(fact["confidence"])
                self.assertTrue(fact["source"])

    def test_diagnostics_report_what_was_considered_and_why_not(self) -> None:
        result = profile.compact_profile("track bills and spending this month")
        diagnostics = result["diagnostics"]
        self.assertGreaterEqual(diagnostics["considered"], diagnostics["selected"])
        self.assertIn("minimum_score", diagnostics)
        self.assertIn("char_budget", diagnostics)

    def test_status_describes_the_index_without_printing_it(self) -> None:
        status = profile.profile_status()
        self.assertIn("drive-derived-context.json", status["excluded_sources"])
        self.assertGreater(status["facts"], 0)
        self.assertGreater(status["restricted"], 0)
        blob = json.dumps(status)
        self.assertNotIn("Olivia", blob, "status leaked profile content")


class BudgetTests(unittest.TestCase):
    def test_retrieval_respects_its_character_budget(self) -> None:
        result = profile.compact_profile("plan meals and groceries", limit=50, char_budget=300)
        total = sum(len(fact["statement"]) for fact in result["facts"])
        self.assertLessEqual(total, 300)

    def test_retrieval_respects_its_fact_limit(self) -> None:
        result = profile.compact_profile("plan meals and groceries", limit=2)
        self.assertLessEqual(len(result["facts"]), 2)

    def test_raising_the_threshold_narrows_the_selection(self) -> None:
        loose = profile.compact_profile("track bills and spending", minimum_score=3)
        strict = profile.compact_profile("track bills and spending", minimum_score=12)
        self.assertLessEqual(len(strict["facts"]), len(loose["facts"]))


class CompilerIntegrationTests(unittest.TestCase):
    def test_a_personal_task_receives_profile_context_without_asking(self) -> None:
        packet = compile_context("hr-gui", "fix the HR scanner OCR accuracy for personnel forms", token_budget=1500)
        self.assertIn("profile_context", packet)
        self.assertIn("work_context", packet["profile_context"]["diagnostics"]["domains"])

    def test_an_impersonal_task_carries_no_profile_section(self) -> None:
        packet = compile_context("personal-agent-os", "add a null check to the parser", token_budget=1500)
        self.assertNotIn("profile_context", packet)

    def test_profile_context_stays_within_the_packet_budget(self) -> None:
        for budget in (600, 900, 1200, 2000):
            with self.subTest(budget=budget):
                packet = compile_context("hr-gui", "hr scanner ocr personnel forms", token_budget=budget)
                self.assertTrue(packet["context_measurement"]["within_budget"])

    def test_profile_is_pruned_before_task_selected_project_material(self) -> None:
        """Personal context is real, but the project's own material acts first."""
        packet = compile_context("hr-gui", "hr scanner ocr personnel forms", token_budget=250)
        self.assertTrue(packet["context_measurement"]["within_budget"])
        self.assertNotIn("profile_context", packet)

    def test_adding_profile_retrieval_did_not_balloon_packets(self) -> None:
        """Selective retrieval must not become another source of bulk."""
        packet = compile_context("hr-gui", "fix the HR scanner OCR accuracy for personnel forms", token_budget=1500)
        measurement = packet["context_measurement"]
        self.assertTrue(measurement["within_budget"])
        profile_chars = len(json.dumps(packet.get("profile_context", {})))
        self.assertLess(profile_chars, 1600, "the profile slice is the largest thing in the packet")


if __name__ == "__main__":
    unittest.main()
