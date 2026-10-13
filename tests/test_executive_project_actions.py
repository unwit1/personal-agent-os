"""Tests for project action planning."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.project_actions import REPEATED_DEFERRAL_THRESHOLD, STALE_DAYS_DEFAULT, is_vague_action, project_next_action, scan


class TestIsVagueAction(unittest.TestCase):
    def test_is_vague_action_tbd(self):
        self.assertTrue(is_vague_action("TBD"))

    def test_is_vague_action_todo(self):
        self.assertTrue(is_vague_action("todo"))

    def test_is_vague_action_none(self):
        self.assertTrue(is_vague_action("none"))

    def test_is_vague_action_continue(self):
        self.assertTrue(is_vague_action("continue"))

    def test_is_vague_action_continue_with_period(self):
        self.assertTrue(is_vague_action("continue."))

    def test_is_vague_action_keep_going(self):
        self.assertTrue(is_vague_action("keep going"))

    def test_is_vague_action_progress(self):
        self.assertTrue(is_vague_action("progress"))

    def test_is_vague_action_misc(self):
        self.assertTrue(is_vague_action("misc"))

    def test_is_vague_action_various(self):
        self.assertTrue(is_vague_action("various"))

    def test_is_vague_action_next_steps(self):
        self.assertTrue(is_vague_action("next steps"))

    def test_is_vague_action_work_on_it(self):
        self.assertTrue(is_vague_action("work on it"))

    def test_is_vague_action_n_a(self):
        self.assertTrue(is_vague_action("n/a"))

    def test_is_vague_action_work_on_prefix(self):
        self.assertTrue(is_vague_action("Work on project X"))

    def test_is_vague_action_continue_working_on_prefix(self):
        self.assertTrue(is_vague_action("continue working on the database schema"))

    def test_is_vague_action_continue_with_prefix(self):
        self.assertTrue(is_vague_action("continue with migration"))

    def test_is_vague_action_look_into_prefix(self):
        self.assertTrue(is_vague_action("look into performance issues"))

    def test_is_vague_action_think_about_prefix(self):
        self.assertTrue(is_vague_action("think about architecture"))

    def test_is_vague_action_make_progress_prefix(self):
        self.assertTrue(is_vague_action("make progress on refactor"))

    def test_is_vague_action_keep_working_on_prefix(self):
        self.assertTrue(is_vague_action("keep working on tests"))

    def test_is_vague_action_progress_on_prefix(self):
        self.assertTrue(is_vague_action("progress on deployment"))

    def test_is_vague_action_continue_on_prefix(self):
        self.assertTrue(is_vague_action("continue on cleanup"))

    def test_is_vague_action_work_on_with_three_words(self):
        self.assertTrue(is_vague_action("work on the release notes"))

    def test_is_vague_action_work_on_with_exclamation(self):
        self.assertTrue(is_vague_action("Work on project X!"))

    def test_is_vague_action_work_on_with_question(self):
        self.assertTrue(is_vague_action("Work on project X?"))

    def test_is_vague_action_write_unit_tests_false(self):
        self.assertFalse(is_vague_action("Write unit tests for scan()"))

    def test_is_vague_action_work_on_too_many_words_false(self):
        self.assertFalse(is_vague_action("Work on the release notes draft for v2 launch"))

    def test_is_vague_action_code_false(self):
        self.assertFalse(is_vague_action("Code"))

    def test_is_vague_action_empty_string_false(self):
        self.assertFalse(is_vague_action(""))

    def test_is_vague_action_whitespace_only_false(self):
        self.assertFalse(is_vague_action("   "))

    def test_is_vague_action_none_type_false(self):
        self.assertFalse(is_vague_action(None))

    def test_is_vague_action_int_false(self):
        self.assertFalse(is_vague_action(123))

    def test_is_vague_action_list_false(self):
        self.assertFalse(is_vague_action([]))

    def test_is_vague_action_case_insensitive(self):
        self.assertTrue(is_vague_action("TODO"))
        self.assertTrue(is_vague_action("TbD"))
        self.assertTrue(is_vague_action("WORK ON project X"))

    def test_is_vague_action_collapse_internal_whitespace(self):
        self.assertTrue(is_vague_action("work  on   project   X"))
        self.assertTrue(is_vague_action("continue  ."))


class TestProjectNextActionBasic(unittest.TestCase):
    def test_project_next_action_minimal_state(self):
        state = {"project": "proj-1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["project"], "proj-1")
        self.assertIsNone(result["status"])
        self.assertIsNone(result["goal"])
        self.assertIsNone(result["current_state"])
        self.assertIsNone(result["next_action"])
        self.assertIsNone(result["next_action_source"])
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["waiting_on"], [])
        self.assertEqual(result["decisions_needed"], [])
        self.assertEqual(result["delegable_work"], [])
        self.assertIsNone(result["updated_at"])
        self.assertIsNone(result["age_days"])
        self.assertEqual(result["flags"], ["no_next_action", "unknown_age"])
        self.assertIsNone(result["suggested_next_action"])

    def test_project_next_action_non_dict_raises_type_error(self):
        with self.assertRaises(TypeError):
            project_next_action("not a dict", today=date(2026, 10, 5))
        with self.assertRaises(TypeError):
            project_next_action(None, today=date(2026, 10, 5))
        with self.assertRaises(TypeError):
            project_next_action([], today=date(2026, 10, 5))

    def test_project_next_action_with_all_fields(self):
        state = {
            "project": "proj-1",
            "status": "active",
            "goal": "Complete the integration",
            "current_state": "Working on database schema",
            "next_action": "Review PR #123",
            "blockers": ["Waiting for API review"],
            "waiting_on": ["Design approval"],
            "decisions_needed": ["Should we migrate data?"],
            "delegable_work": ["Unit tests"],
            "updated_at": "2026-09-30T10:00:00Z",
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["project"], "proj-1")
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["goal"], "Complete the integration")
        self.assertEqual(result["current_state"], "Working on database schema")
        self.assertEqual(result["next_action"], "Review PR #123")
        self.assertEqual(result["next_action_source"], "next_action")
        self.assertEqual(result["blockers"], ["Waiting for API review"])
        self.assertEqual(result["waiting_on"], ["Design approval"])
        self.assertEqual(result["decisions_needed"], ["Should we migrate data?"])
        self.assertEqual(result["delegable_work"], ["Unit tests"])
        self.assertEqual(result["updated_at"], "2026-09-30T10:00:00Z")
        self.assertEqual(result["age_days"], 5)


class TestGoalExtraction(unittest.TestCase):
    def test_goal_from_goal_field(self):
        state = {"project": "p1", "goal": "Implement feature X"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["goal"], "Implement feature X")

    def test_goal_from_summary_when_goal_empty(self):
        state = {"project": "p1", "goal": "", "summary": "Fallback summary"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["goal"], "Fallback summary")

    def test_goal_from_summary_when_goal_missing(self):
        state = {"project": "p1", "summary": "Fallback summary"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["goal"], "Fallback summary")

    def test_goal_none_when_both_missing(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["goal"])

    def test_goal_whitespace_only_treated_as_empty(self):
        state = {"project": "p1", "goal": "   ", "summary": "Fallback"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["goal"], "Fallback")

    def test_goal_non_string_ignored(self):
        state = {"project": "p1", "goal": 123, "summary": "Fallback"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["goal"], "Fallback")


class TestCurrentStateExtraction(unittest.TestCase):
    def test_current_state_present(self):
        state = {"project": "p1", "current_state": "In progress"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["current_state"], "In progress")

    def test_current_state_empty_becomes_none(self):
        state = {"project": "p1", "current_state": ""}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["current_state"])

    def test_current_state_whitespace_becomes_none(self):
        state = {"project": "p1", "current_state": "   "}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["current_state"])

    def test_current_state_missing_is_none(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["current_state"])

    def test_current_state_non_string_becomes_none(self):
        state = {"project": "p1", "current_state": 123}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["current_state"])


class TestNextActionExtraction(unittest.TestCase):
    def test_next_action_from_next_action_field(self):
        state = {"project": "p1", "next_action": "Deploy to staging"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["next_action"], "Deploy to staging")
        self.assertEqual(result["next_action_source"], "next_action")

    def test_next_action_from_current_priorities_first_non_empty(self):
        state = {
            "project": "p1",
            "current_priorities": ["Write tests", "Review docs"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["next_action"], "Write tests")
        self.assertEqual(result["next_action_source"], "current_priorities")

    def test_next_action_skips_empty_priorities(self):
        state = {
            "project": "p1",
            "current_priorities": ["", "   ", "Fix bugs"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["next_action"], "Fix bugs")
        self.assertEqual(result["next_action_source"], "current_priorities")

    def test_next_action_from_next_action_takes_priority(self):
        state = {
            "project": "p1",
            "next_action": "Priority action",
            "current_priorities": ["Fallback action"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["next_action"], "Priority action")
        self.assertEqual(result["next_action_source"], "next_action")

    def test_next_action_none_when_all_empty(self):
        state = {"project": "p1", "current_priorities": ["", "   "]}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["next_action"])
        self.assertIsNone(result["next_action_source"])

    def test_next_action_none_when_missing(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["next_action"])
        self.assertIsNone(result["next_action_source"])

    def test_next_action_empty_string_ignored(self):
        state = {"project": "p1", "next_action": ""}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["next_action"])
        self.assertIsNone(result["next_action_source"])

    def test_next_action_non_list_priorities_ignored(self):
        state = {"project": "p1", "current_priorities": "not a list"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["next_action"])


class TestListFieldExtraction(unittest.TestCase):
    def test_blockers_extracted_in_order(self):
        state = {
            "project": "p1",
            "blockers": ["Issue A", "Issue B", "Issue C"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["blockers"], ["Issue A", "Issue B", "Issue C"])

    def test_blockers_empty_strings_filtered(self):
        state = {
            "project": "p1",
            "blockers": ["Issue A", "", "   ", "Issue B"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["blockers"], ["Issue A", "Issue B"])

    def test_blockers_non_strings_filtered(self):
        state = {
            "project": "p1",
            "blockers": ["Issue A", 123, None, "Issue B"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["blockers"], ["Issue A", "Issue B"])

    def test_blockers_non_list_becomes_empty_list(self):
        state = {"project": "p1", "blockers": "not a list"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["blockers"], [])

    def test_waiting_on_extracted(self):
        state = {"project": "p1", "waiting_on": ["Approval", "Feedback"]}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["waiting_on"], ["Approval", "Feedback"])

    def test_decisions_needed_extracted(self):
        state = {"project": "p1", "decisions_needed": ["Choose tech stack", "Define scope"]}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["decisions_needed"], ["Choose tech stack", "Define scope"])

    def test_delegable_work_extracted(self):
        state = {"project": "p1", "delegable_work": ["Write docs", "Review code"]}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["delegable_work"], ["Write docs", "Review code"])

    def test_all_list_fields_missing_returns_empty_lists(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["waiting_on"], [])
        self.assertEqual(result["decisions_needed"], [])
        self.assertEqual(result["delegable_work"], [])


class TestAgeDaysCalculation(unittest.TestCase):
    def test_age_days_calculated_from_updated_at(self):
        state = {"project": "p1", "updated_at": "2026-10-01T10:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["age_days"], 4)

    def test_age_days_zero_when_same_day(self):
        state = {"project": "p1", "updated_at": "2026-10-05T10:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["age_days"], 0)

    def test_age_days_large_value(self):
        state = {"project": "p1", "updated_at": "2026-01-01T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["age_days"], 277)

    def test_age_days_none_when_updated_at_missing(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["age_days"])

    def test_age_days_none_when_updated_at_unparsable(self):
        state = {"project": "p1", "updated_at": "not a date"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["age_days"])

    def test_age_days_none_when_updated_at_too_short(self):
        state = {"project": "p1", "updated_at": "2026-10"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["age_days"])

    def test_age_days_none_when_updated_at_non_string(self):
        state = {"project": "p1", "updated_at": 12345}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["age_days"])


class TestFlagsGeneration(unittest.TestCase):
    def test_deferral_threshold_flags_and_sorts(self):
        state = {"project": "p1", "decisions_needed": ["Choice"]}
        default = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(default["deferrals"], 0)
        self.assertNotIn("repeatedly_deferred", default["flags"])

        below = project_next_action(state, today=date(2026, 10, 5), deferrals=2)
        self.assertNotIn("repeatedly_deferred", below["flags"])

        at_threshold = project_next_action(state, today=date(2026, 10, 5), deferrals=3)
        self.assertIn("repeatedly_deferred", at_threshold["flags"])
        self.assertEqual(at_threshold["flags"], sorted(at_threshold["flags"]))
        self.assertEqual(REPEATED_DEFERRAL_THRESHOLD, 3)

    def test_flag_no_next_action(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("no_next_action", result["flags"])

    def test_flag_no_next_action_absent_when_next_action_present(self):
        state = {"project": "p1", "next_action": "Do something"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertNotIn("no_next_action", result["flags"])

    def test_flag_stalled(self):
        state = {"project": "p1", "updated_at": "2026-08-01T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("stalled", result["flags"])

    def test_flag_stalled_not_present_when_within_threshold(self):
        state = {"project": "p1", "updated_at": "2026-09-30T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5), stale_days=10)
        self.assertNotIn("stalled", result["flags"])

    def test_flag_stalled_one_day_over_threshold(self):
        state = {"project": "p1", "updated_at": "2026-09-04T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5), stale_days=30)
        self.assertIn("stalled", result["flags"])

    def test_flag_not_stalled_at_exact_threshold(self):
        state = {"project": "p1", "updated_at": "2026-09-05T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5), stale_days=30)
        self.assertEqual(result["age_days"], 30)
        self.assertNotIn("stalled", result["flags"])

    def test_flag_stalled_just_under_threshold(self):
        state = {"project": "p1", "updated_at": "2026-09-06T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5), stale_days=30)
        self.assertNotIn("stalled", result["flags"])

    def test_flag_unknown_age(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("unknown_age", result["flags"])

    def test_flag_unknown_age_absent_when_age_known(self):
        state = {"project": "p1", "updated_at": "2026-10-01T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertNotIn("unknown_age", result["flags"])

    def test_flag_blocked_with_blockers(self):
        state = {"project": "p1", "blockers": ["Issue A"]}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("blocked", result["flags"])

    def test_flag_blocked_with_waiting_on(self):
        state = {"project": "p1", "waiting_on": ["Approval"]}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("blocked", result["flags"])

    def test_flag_blocked_with_both(self):
        state = {
            "project": "p1",
            "blockers": ["Issue A"],
            "waiting_on": ["Approval"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("blocked", result["flags"])

    def test_flag_blocked_absent_when_none(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertNotIn("blocked", result["flags"])

    def test_flag_needs_decision(self):
        state = {"project": "p1", "decisions_needed": ["Choose tech"]}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("needs_decision", result["flags"])

    def test_flag_needs_decision_absent_when_none(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertNotIn("needs_decision", result["flags"])

    def test_flags_sorted(self):
        state = {
            "project": "p1",
            "decisions_needed": ["Choice"],
            "blockers": ["Issue"],
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["flags"], sorted(result["flags"]))

    def test_multiple_flags_combined(self):
        state = {
            "project": "p1",
            "next_action": "Do something",
            "decisions_needed": ["Choice"],
            "blockers": ["Issue"],
            "updated_at": "2026-08-01T00:00:00Z",
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        expected_flags = ["blocked", "needs_decision", "stalled"]
        self.assertEqual(result["flags"], expected_flags)


class TestVagueNextAction(unittest.TestCase):
    def test_vague_next_action_flag_set_for_tbd(self):
        state = {"project": "p1", "next_action": "TBD"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("vague_next_action", result["flags"])

    def test_vague_next_action_flag_set_for_work_on_prefix(self):
        state = {"project": "p1", "next_action": "Work on project X"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("vague_next_action", result["flags"])

    def test_vague_next_action_flag_not_set_for_specific_action(self):
        state = {"project": "p1", "next_action": "Write unit tests for scan()"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertNotIn("vague_next_action", result["flags"])

    def test_vague_next_action_flag_not_set_when_no_next_action(self):
        state = {"project": "p1"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertNotIn("vague_next_action", result["flags"])

    def test_suggested_next_action_none_when_not_vague(self):
        state = {"project": "p1", "next_action": "Write tests"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["suggested_next_action"])

    def test_suggested_next_action_from_current_priorities(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "current_priorities": ["Write tests", "Review docs"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["suggested_next_action"], "Write tests")

    def test_suggested_next_action_skips_vague_in_priorities(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "current_priorities": ["continue", "Write tests", "Review docs"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["suggested_next_action"], "Write tests")

    def test_suggested_next_action_skips_entry_equal_to_next_action(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "current_priorities": ["TBD", "Write tests", "Review docs"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["suggested_next_action"], "Write tests")

    def test_suggested_next_action_skips_empty_priorities(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "current_priorities": ["", "Write tests", "Review docs"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["suggested_next_action"], "Write tests")

    def test_suggested_next_action_from_delegable_work(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "current_priorities": [],
            "delegable_work": ["Unit tests", "Code review"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["suggested_next_action"], "Unit tests")

    def test_suggested_next_action_from_delegable_work_skips_vague(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "current_priorities": [],
            "delegable_work": ["work on it", "Code review"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["suggested_next_action"], "Code review")

    def test_suggested_next_action_none_when_all_vague(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "current_priorities": ["continue", "todo"],
            "delegable_work": ["progress", "work on it"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["suggested_next_action"])

    def test_suggested_next_action_none_when_empty_priorities_and_work(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "current_priorities": [],
            "delegable_work": []
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["suggested_next_action"])

    def test_vague_next_action_flag_with_multiple_other_flags(self):
        state = {
            "project": "p1",
            "next_action": "TBD",
            "decisions_needed": ["Choose tech"],
            "blockers": ["Issue"]
        }
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIn("vague_next_action", result["flags"])
        self.assertIn("blocked", result["flags"])
        self.assertIn("needs_decision", result["flags"])
        self.assertEqual(result["flags"], sorted(result["flags"]))


class TestScanBasic(unittest.TestCase):
    def test_scan_repeated_deferrals(self):
        states = [
            {"project": "a", "status": "active"},
            {"project": "b", "status": "active"},
        ]
        result = scan(states, today=date(2026, 10, 5), deferrals={"a": 3, "b": 1})
        self.assertEqual(result["repeatedly_deferred"], ["a"])
        projects = {p["project"]: p for p in result["projects"]}
        self.assertEqual(projects["b"]["deferrals"], 1)

    def test_scan_without_deferrals_has_no_repeatedly_deferred_projects(self):
        result = scan([{"project": "a", "status": "active"}], today=date(2026, 10, 5))
        self.assertEqual(result["repeatedly_deferred"], [])

    def test_scan_empty_list(self):
        result = scan([], today=date(2026, 10, 5))
        self.assertEqual(result["projects"], [])
        self.assertEqual(result["blocked"], [])
        self.assertEqual(result["stalled"], [])
        self.assertEqual(result["no_next_action"], [])
        self.assertEqual(result["needs_decision"], [])
        self.assertEqual(result["stale_days"], STALE_DAYS_DEFAULT)

    def test_scan_filters_non_dicts(self):
        states = [
            {"project": "p1", "status": "active"},
            "not a dict",
            None,
            {"project": "p2", "status": "active"},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(len(result["projects"]), 2)
        self.assertEqual(result["projects"][0]["project"], "p1")
        self.assertEqual(result["projects"][1]["project"], "p2")

    def test_scan_filters_inactive_by_default(self):
        states = [
            {"project": "p1", "status": "active"},
            {"project": "p2", "status": "inactive"},
            {"project": "p3", "status": "active"},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(len(result["projects"]), 2)
        self.assertNotIn("p2", [p["project"] for p in result["projects"]])

    def test_scan_includes_inactive_when_flag_set(self):
        states = [
            {"project": "p1", "status": "active"},
            {"project": "p2", "status": "inactive"},
            {"project": "p3", "status": "archived"},
        ]
        result = scan(states, today=date(2026, 10, 5), include_inactive=True)
        self.assertEqual(len(result["projects"]), 3)

    def test_scan_projects_sorted_by_id(self):
        states = [
            {"project": "c", "status": "active"},
            {"project": "a", "status": "active"},
            {"project": "b", "status": "active"},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(
            [p["project"] for p in result["projects"]],
            ["a", "b", "c"]
        )

    def test_scan_stalled_list(self):
        states = [
            {"project": "p1", "status": "active", "updated_at": "2026-08-01T00:00:00Z"},
            {"project": "p2", "status": "active", "updated_at": "2026-10-01T00:00:00Z"},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(result["stalled"], ["p1"])

    def test_scan_no_next_action_list(self):
        states = [
            {"project": "p1", "status": "active", "next_action": "Do this"},
            {"project": "p2", "status": "active"},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(result["no_next_action"], ["p2"])

    def test_scan_needs_decision_list(self):
        states = [
            {"project": "p1", "status": "active"},
            {"project": "p2", "status": "active", "decisions_needed": ["Choose tech"]},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(result["needs_decision"], ["p2"])

    def test_scan_blocked_list_uses_normalized_dependencies_and_order(self):
        states = [
            {"project": "z", "status": "active", "waiting_on": ["Review"]},
            {"project": "c", "status": "active", "blockers": ["Issue"], "waiting_on": ["Approval"]},
            {"project": "b", "status": "active", "blockers": ["Issue"]},
            {"project": "a", "status": "active", "blockers": "malformed", "waiting_on": [None, "  "]},
            {"project": "d", "status": "active", "blockers": [], "waiting_on": []},
        ]
        original = [dict(state) for state in states]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(result["blocked"], ["b", "c", "z"])
        self.assertEqual(states, original)

    def test_scan_blocked_respects_inactive_filter(self):
        states = [
            {"project": "active", "status": "active", "blockers": ["Issue"]},
            {"project": "inactive", "status": "inactive", "waiting_on": ["Approval"]},
        ]
        self.assertEqual(scan(states, today=date(2026, 10, 5))["blocked"], ["active"])
        self.assertEqual(
            scan(states, today=date(2026, 10, 5), include_inactive=True)["blocked"],
            ["active", "inactive"],
        )

    def test_scan_custom_stale_days(self):
        result = scan([], today=date(2026, 10, 5), stale_days=60)
        self.assertEqual(result["stale_days"], 60)

    def test_scan_returns_full_project_results(self):
        state = {
            "project": "p1",
            "status": "active",
            "goal": "Complete feature",
            "next_action": "Review PR",
            "updated_at": "2026-10-01T00:00:00Z",
        }
        result = scan([state], today=date(2026, 10, 5))
        self.assertEqual(len(result["projects"]), 1)
        project = result["projects"][0]
        self.assertEqual(project["project"], "p1")
        self.assertEqual(project["goal"], "Complete feature")
        self.assertEqual(project["age_days"], 4)

    def test_scan_vague_next_action_list(self):
        states = [
            {"project": "p1", "status": "active", "next_action": "TBD"},
            {"project": "p2", "status": "active", "next_action": "Write tests"},
            {"project": "p3", "status": "active", "next_action": "Work on project X"},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(set(result["vague_next_action"]), {"p1", "p3"})

    def test_scan_vague_next_action_empty_when_none(self):
        states = [
            {"project": "p1", "status": "active", "next_action": "Write tests"},
            {"project": "p2", "status": "active", "next_action": "Review code"},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(result["vague_next_action"], [])


class TestScanEdgeCases(unittest.TestCase):
    def test_scan_no_status_field_not_included_by_default(self):
        states = [
            {"project": "p1"},
            {"project": "p2", "status": "active"},
        ]
        result = scan(states, today=date(2026, 10, 5))
        self.assertEqual(len(result["projects"]), 1)
        self.assertEqual(result["projects"][0]["project"], "p2")

    def test_scan_multiple_flags_per_project(self):
        state = {
            "project": "p1",
            "status": "active",
            "decisions_needed": ["Choose"],
            "blockers": ["Issue"],
            "updated_at": "2026-08-01T00:00:00Z",
        }
        result = scan([state], today=date(2026, 10, 5))
        self.assertIn("p1", result["stalled"])
        self.assertIn("p1", result["needs_decision"])

    def test_scan_project_with_all_flags_appears_in_all_lists(self):
        state = {
            "project": "p1",
            "status": "active",
            "next_action": "Do something",
            "updated_at": "2026-08-01T00:00:00Z",
            "decisions_needed": ["Choice"],
        }
        result = scan([state], today=date(2026, 10, 5))
        self.assertIn("p1", result["stalled"])
        self.assertIn("p1", result["needs_decision"])
        self.assertNotIn("p1", result["no_next_action"])


class TestStaleDefaultConstant(unittest.TestCase):
    def test_stale_days_default_value(self):
        self.assertEqual(STALE_DAYS_DEFAULT, 30)

    def test_stale_days_default_used_in_project_next_action(self):
        state = {"project": "p1", "updated_at": "2026-09-06T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertNotIn("stalled", result["flags"])

    def test_stale_days_default_used_in_scan(self):
        state = {"project": "p1", "status": "active", "updated_at": "2026-09-06T00:00:00Z"}
        result = scan([state], today=date(2026, 10, 5))
        self.assertEqual(result["stale_days"], STALE_DAYS_DEFAULT)
        self.assertNotIn("p1", result["stalled"])


if __name__ == "__main__":
    unittest.main()
