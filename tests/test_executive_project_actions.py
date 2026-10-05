"""Tests for project action planning."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.project_actions import STALE_DAYS_DEFAULT, project_next_action, scan


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

    def test_age_days_parses_only_first_10_chars(self):
        state = {"project": "p1", "updated_at": "2026-10-01T10:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertEqual(result["age_days"], 4)

    def test_age_days_none_when_updated_at_too_short(self):
        state = {"project": "p1", "updated_at": "2026-10"}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["age_days"])

    def test_age_days_none_when_updated_at_non_string(self):
        state = {"project": "p1", "updated_at": 12345}
        result = project_next_action(state, today=date(2026, 10, 5))
        self.assertIsNone(result["age_days"])


class TestFlagsGeneration(unittest.TestCase):
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

    def test_flag_stalled_threshold_boundary(self):
        state = {"project": "p1", "updated_at": "2026-09-04T00:00:00Z"}
        result = project_next_action(state, today=date(2026, 10, 5), stale_days=30)
        self.assertIn("stalled", result["flags"])

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


class TestScanBasic(unittest.TestCase):
    def test_scan_empty_list(self):
        result = scan([], today=date(2026, 10, 5))
        self.assertEqual(result["projects"], [])
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
