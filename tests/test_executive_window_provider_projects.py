"""Tests for project provider: project queue items from state."""

from __future__ import annotations

import sys
import hashlib
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window.providers_projects import project_items
from agent_os.executive.window_queue import queue_item_from_window_item


class ProjectItemsTests(unittest.TestCase):
    """Tests for project_items() with injected load_projects and fixed today."""

    def _make_registry_entry(
        self, project_id: str = "p1", name: str = "Project 1", tab: str = "work"
    ) -> dict:
        """Helper to create a minimal registry entry."""
        return {"id": project_id, "name": name, "tab": tab, "state_file": f"projects/{project_id}/state.json"}

    def _make_state(
        self,
        project: str = "p1",
        status: str = "active",
        updated_at: str = "2026-09-30T10:00:00Z",
        decisions_needed: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """Helper to create a minimal project state."""
        result = {
            "project": project,
            "status": status,
            "updated_at": updated_at,
        }
        if decisions_needed:
            result["decisions_needed"] = decisions_needed
        result.update(kwargs)
        return result

    def test_no_projects_produce_no_items(self):
        """Empty project list produces no items."""
        items = project_items(lambda: [], today=date(2026, 10, 5))
        self.assertEqual(items, [])

    def test_inactive_projects_ignored(self):
        """Projects with status != 'active' are skipped."""
        entry = self._make_registry_entry()
        state = self._make_state(status="inactive")
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertEqual(items, [])

    def test_active_project_with_no_flags_produces_no_items(self):
        """An active project without any flags produces no items."""
        entry = self._make_registry_entry()
        state = self._make_state(next_action="Do something")
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertEqual(items, [])

    def test_single_decision_produces_decision_item(self):
        """A project with one decision_needed produces a decision item (and no_next_action if no next_action)."""
        entry = self._make_registry_entry()
        state = self._make_state(decisions_needed=["Should we refactor?"])
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        # Project has needs_decision and no_next_action flags, so 2 items
        self.assertEqual(len(items), 2)
        decision_item = [i for i in items if i["kind"] == "project_decision"][0]
        self.assertEqual(decision_item["title"], "Should we refactor?")
        self.assertIn("Decision needed for", decision_item["why"])
        self.assertEqual(decision_item["score"], 3)
        self.assertEqual(decision_item["tab"], "work")
        self.assertEqual(decision_item["source"], "Project p1")
        self.assertIn("project", decision_item["context"])

    def test_decision_text_is_in_context(self):
        """Decision items expose their decision text in context."""
        entry = self._make_registry_entry(project_id="db-project")
        state = self._make_state(project="db-project", decisions_needed=["Pick a database"])
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        decision_item = next(item for item in items if item["kind"] == "project_decision")
        self.assertEqual(
            decision_item["context"],
            {"project": "db-project", "decision": "Pick a database"},
        )

    def test_multiple_decisions_produce_multiple_items(self):
        """A project with two decisions produces two decision items (plus no_next_action if applicable)."""
        entry = self._make_registry_entry()
        state = self._make_state(
            decisions_needed=["Decision 1", "Decision 2"]
        )
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        # 2 decision items + 1 no_next_action item = 3 items total
        self.assertEqual(len(items), 3)
        decision_items = [i for i in items if i["kind"] == "project_decision"]
        self.assertEqual(len(decision_items), 2)
        titles = {item["title"] for item in decision_items}
        self.assertEqual(titles, {"Decision 1", "Decision 2"})

    def test_decision_id_hash_deterministic(self):
        """Decision items have stable, deterministic ids based on text hash."""
        entry = self._make_registry_entry()
        state = self._make_state(decisions_needed=["Fix the bug"])
        items1 = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        items2 = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertEqual(items1[0]["id"], items2[0]["id"])
        self.assertTrue(items1[0]["id"].startswith("project:p1:decision:"))

    def test_duplicate_normalized_decisions_have_one_item_and_queue_identity(self):
        entry = self._make_registry_entry(tab="personal")
        state = self._make_state(
            next_action="Write release notes",
            decisions_needed=["  Choose a database  ", "Choose a database", "  Choose a database\t"],
        )
        items = project_items(
            lambda: [(entry, state)], today=date(2026, 10, 5),
            deferral_counts=lambda: {},
        )
        decisions = [item for item in items if item["kind"] == "project_decision"]
        self.assertEqual(len(decisions), 1)
        decision = decisions[0]
        trimmed = "Choose a database"
        expected_id = f"project:p1:decision:{hashlib.sha1(trimmed.encode('utf-8')).hexdigest()[:10]}"
        self.assertEqual(decision["id"], expected_id)
        self.assertEqual(decision["title"], trimmed)
        self.assertEqual(decision["context"]["decision"], trimmed)
        self.assertEqual(decision["score"], 3)
        self.assertEqual(decision["tab"], "personal")
        queue_items = [queue_item_from_window_item(item, "projects", queued_at="2026-10-05T00:00:00Z") for item in decisions]
        self.assertEqual(len({item["id"] for item in queue_items}), 1)
        self.assertEqual(len({item["entity_id"] for item in queue_items}), 1)

    def test_distinct_decisions_keep_order_score_and_project_tab(self):
        entry = self._make_registry_entry(tab="work")
        state = self._make_state(
            next_action="Write release notes",
            decisions_needed=["First decision", "Second decision", "Third decision"],
        )
        items = project_items(
            lambda: [(entry, state)], today=date(2026, 10, 5),
            deferral_counts=lambda: {},
        )
        decisions = [item for item in items if item["kind"] == "project_decision"]
        self.assertEqual([item["title"] for item in decisions], state["decisions_needed"])
        self.assertEqual([item["score"] for item in decisions], [3, 3, 3])
        self.assertEqual([item["tab"] for item in decisions], ["work", "work", "work"])

    def test_repeated_normalized_blockers_and_waiting_on_are_listed_once(self):
        entry = self._make_registry_entry()
        state = self._make_state(
            next_action="Resolve dependency",
            blockers=[" Vendor ", "Vendor", "Approval", " Approval "],
            waiting_on=[" Review ", "Review", "Legal", " Legal "],
        )
        items = project_items(
            lambda: [(entry, state)], today=date(2026, 10, 5),
            deferral_counts=lambda: {},
        )
        blocked = next(item for item in items if item["kind"] == "project_blocked")
        self.assertEqual(
            blocked["why"],
            "Blocked by: Vendor; Approval | Waiting on: Review; Legal",
        )

    def test_stalled_project_produces_item(self):
        """A project without update for > stale_days produces a stalled item."""
        entry = self._make_registry_entry()
        state = self._make_state(
            updated_at="2026-09-01T10:00:00Z", next_action="Do something"
        )
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5), stale_days=30)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["kind"], "project_stalled")
        self.assertIn("is stalled", item["title"])
        self.assertEqual(item["score"], 2)
        self.assertIn("age_days", item)

    def test_blocked_project_details_and_stable_id(self):
        entry = self._make_registry_entry("p-blocked", "Blocked project", "personal")
        def items(blockers, waiting_on):
            state = self._make_state(project="p-blocked", next_action="Do work", blockers=blockers, waiting_on=waiting_on)
            return project_items(lambda: [(entry, state)], today=date(2026, 10, 5))

        blockers_only = next(i for i in items(["Vendor", "Approval"], []) if i["kind"] == "project_blocked")
        self.assertEqual(blockers_only["why"], "Blocked by: Vendor; Approval")
        waiting_only = next(i for i in items([], ["Review"]) if i["kind"] == "project_blocked")
        self.assertEqual(waiting_only["why"], "Waiting on: Review")
        both = [i for i in items(["Vendor"], ["Review"]) if i["kind"] == "project_blocked"]
        self.assertEqual(len(both), 1)
        self.assertEqual(both[0]["why"], "Blocked by: Vendor | Waiting on: Review")
        self.assertEqual(both[0]["id"], "project:p-blocked:blocked")
        self.assertEqual(both[0]["title"], "Blocked project is blocked")
        self.assertEqual(both[0]["score"], 2)
        self.assertEqual(both[0]["context"], {"project": "p-blocked"})
        self.assertEqual(both[0]["tab"], "personal")
        changed_text = [i for i in items(["Different"], ["Other"]) if i["kind"] == "project_blocked"]
        self.assertEqual(changed_text[0]["id"], both[0]["id"])

    def test_empty_or_invalid_blocking_lists_emit_no_item(self):
        entry = self._make_registry_entry()
        for blockers, waiting_on in (([], []), (None, {}), ("bad", [None, 3]), ([" ", 1], [])):
            state = self._make_state(blockers=blockers, waiting_on=waiting_on, next_action="Do work")
            self.assertFalse(any(i["kind"] == "project_blocked" for i in project_items(
                lambda: [(entry, state)], today=date(2026, 10, 5)
            )))

    def test_blocked_items_respect_inactive_filter_and_coexist_in_order(self):
        entry = self._make_registry_entry()
        inactive = self._make_state(status="inactive", blockers=["X"])
        self.assertEqual(project_items(lambda: [(entry, inactive)], today=date(2026, 10, 5)), [])
        state = self._make_state(
            updated_at="2026-08-01T10:00:00Z", decisions_needed=["Choose"],
            blockers=["X"], waiting_on=["Y"], next_action="Do work",
        )
        result = project_items(lambda: [(entry, state)], today=date(2026, 10, 5), stale_days=30,
                               deferral_counts=lambda: {"p1": 3})
        kinds = [i["kind"] for i in result]
        self.assertEqual(kinds, ["project_decision", "project_stalled", "project_blocked", "project_repeatedly_deferred"])

    def test_no_next_action_produces_item(self):
        """A project without next_action produces a no_next_action item."""
        entry = self._make_registry_entry()
        state = self._make_state()
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["kind"], "project_no_next_action")
        self.assertIn("has no next action", item["title"])
        self.assertEqual(item["score"], 1)

    def test_vague_next_action_suggests_concrete_priority(self):
        entry = self._make_registry_entry("p-vague")
        state = self._make_state(
            project="p-vague",
            next_action="Work on project X",
            current_priorities=["Work on project X", "Write release notes"],
        )
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "project:p-vague:vague-next-action")
        self.assertEqual(items[0]["score"], 1)
        self.assertEqual(items[0]["kind"], "project_vague_next_action")
        self.assertIn("Write release notes", items[0]["why"])

    def test_vague_next_action_without_alternative_requests_concrete_step(self):
        entry = self._make_registry_entry()
        state = self._make_state(next_action="Work on project X")
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        vague_item = next(i for i in items if i["kind"] == "project_vague_next_action")
        self.assertIn("record a concrete next step", vague_item["why"])

    def test_concrete_next_action_has_no_vague_item(self):
        entry = self._make_registry_entry()
        state = self._make_state(next_action="Write release notes")
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertFalse(any(i["kind"] == "project_vague_next_action" for i in items))

    def test_repeatedly_deferred_project_emits_item_at_threshold(self):
        entry = self._make_registry_entry()
        state = self._make_state(next_action="Write release notes")
        items = project_items(
            lambda: [(entry, state)], today=date(2026, 10, 5),
            deferral_counts=lambda: {"p1": 3},
        )
        deferred = [i for i in items if i["kind"] == "project_repeatedly_deferred"]
        self.assertEqual(len(deferred), 1)
        self.assertEqual(deferred[0]["score"], 2)
        self.assertTrue(deferred[0]["why"].startswith("Deferred 3 times"))

    def test_repeatedly_deferred_below_threshold_emits_no_item(self):
        entry = self._make_registry_entry()
        state = self._make_state(next_action="Write release notes")
        items = project_items(
            lambda: [(entry, state)], today=date(2026, 10, 5),
            deferral_counts=lambda: {"p1": 2},
        )
        self.assertFalse(any(i["kind"] == "project_repeatedly_deferred" for i in items))

    def test_failing_deferral_counts_matches_no_deferrals(self):
        entry = self._make_registry_entry()
        state = self._make_state(next_action="Write release notes")
        load = lambda: [(entry, state)]
        expected = project_items(load, today=date(2026, 10, 5), deferral_counts=lambda: {})

        def fail():
            raise RuntimeError("event bus unavailable")

        actual = project_items(load, today=date(2026, 10, 5), deferral_counts=fail)
        self.assertEqual(actual, expected)

    def test_deferrals_for_other_project_do_not_affect_project(self):
        entry = self._make_registry_entry()
        state = self._make_state(next_action="Write release notes")
        items = project_items(
            lambda: [(entry, state)], today=date(2026, 10, 5),
            deferral_counts=lambda: {"other": 3},
        )
        self.assertFalse(any(i["kind"] == "project_repeatedly_deferred" for i in items))

    def test_vague_next_action_respects_personal_tab(self):
        entry = self._make_registry_entry(tab="personal")
        state = self._make_state(next_action="Work on project X")
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        vague_item = next(i for i in items if i["kind"] == "project_vague_next_action")
        self.assertEqual(vague_item["tab"], "personal")

    def test_project_with_current_priorities_is_not_stalled(self):
        """A project with current_priorities (fallback to next_action) is not flagged no_next_action."""
        entry = self._make_registry_entry()
        state = self._make_state(current_priorities=["Priority 1"])
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertEqual(items, [])

    def test_tab_personal_when_entry_tab_is_personal(self):
        """Items inherit tab='personal' from registry entry."""
        entry = self._make_registry_entry(tab="personal")
        state = self._make_state()
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertEqual(items[0]["tab"], "personal")

    def test_tab_work_by_default(self):
        """Items default to tab='work' unless entry specifies personal."""
        entry = self._make_registry_entry()
        state = self._make_state()
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertEqual(items[0]["tab"], "work")

    def test_name_from_entry_or_falls_back_to_pid(self):
        """Item 'why' uses entry name; falls back to project id if name missing."""
        entry = self._make_registry_entry(name="Custom Name")
        state = self._make_state(decisions_needed=["A decision"])
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        decision_item = [i for i in items if i["kind"] == "project_decision"][0]
        self.assertIn("Custom Name", decision_item["why"])

    def test_name_falls_back_to_pid_when_missing(self):
        """Item uses project id when entry name is missing."""
        entry = {"id": "pid-1", "state_file": "x"}
        state = self._make_state(project="pid-1", decisions_needed=["A decision"])
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        decision_item = [i for i in items if i["kind"] == "project_decision"][0]
        self.assertIn("pid-1", decision_item["why"])

    def test_age_days_included_when_int(self):
        """age_days is included in items when project_next_action returns an int."""
        entry = self._make_registry_entry()
        state = self._make_state(updated_at="2026-09-30T10:00:00Z")
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertIn("age_days", items[0])
        self.assertEqual(items[0]["age_days"], 5)

    def test_age_days_omitted_when_none(self):
        """age_days key is omitted from items when project_next_action returns None."""
        entry = self._make_registry_entry()
        state = self._make_state(updated_at=None)
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertNotIn("age_days", items[0])

    def test_multiple_projects_sorted_by_pid(self):
        """Multiple projects are sorted by project id in output."""
        entries = [
            self._make_registry_entry("z-project", "Z"),
            self._make_registry_entry("a-project", "A"),
            self._make_registry_entry("m-project", "M"),
        ]
        states = [
            self._make_state(project="z-project"),
            self._make_state(project="a-project"),
            self._make_state(project="m-project"),
        ]
        load_func = lambda: list(zip(entries, states))
        items = project_items(load_func, today=date(2026, 10, 5))
        # Extract project ids from source field (or context).
        projects_in_order = [item["context"]["project"] for item in items]
        self.assertEqual(projects_in_order, ["a-project", "m-project", "z-project"])

    def test_duplicate_project_ids_keep_first_registry_entry(self):
        first = self._make_registry_entry(name="First")
        second = self._make_registry_entry(name="Second")
        state = self._make_state()
        items = project_items(lambda: [(first, state), (second, state)], today=date(2026, 10, 5))
        self.assertEqual([item["title"] for item in items], ["First has no next action"])

    def test_project_id_from_entry_when_state_missing(self):
        """Project id uses entry['id'] if state['project'] is missing."""
        entry = self._make_registry_entry("entry-id")
        state = {"status": "active"}
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertIn("entry-id", items[0]["source"])

    def test_project_id_from_state_when_both_present(self):
        """Project id prefers state['project'] over entry['id']."""
        entry = self._make_registry_entry("entry-id")
        state = self._make_state(project="state-id")
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertIn("state-id", items[0]["source"])

    def test_items_from_same_project_sorted_by_score_descending(self):
        """Items from one project are ordered: decisions (3), stalled (2), no-next-action (1)."""
        entry = self._make_registry_entry()
        state = self._make_state(
            updated_at="2026-08-01T10:00:00Z",  # Very stale
            decisions_needed=["Decision A"],
        )
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5), stale_days=30)
        self.assertEqual(
            [item["kind"] for item in items],
            ["project_decision", "project_stalled", "project_no_next_action"],
        )
        self.assertEqual([item["score"] for item in items], [3, 2, 1])

    def test_required_fields_present(self):
        """Every item has id, kind, title, why, score, tab, source, context."""
        entry = self._make_registry_entry()
        state = self._make_state()
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertGreater(len(items), 0)
        required = {"id", "kind", "title", "why", "score", "tab", "source", "context"}
        for item in items:
            self.assertTrue(required.issubset(item.keys()), f"Missing fields in {item}")

    def test_default_today_is_date_today(self):
        """When today=None, defaults to date.today()."""
        entry = self._make_registry_entry()
        state = self._make_state()
        items = project_items(lambda: [(entry, state)])
        self.assertGreater(len(items), 0)

    def test_default_stale_days(self):
        """When stale_days is omitted, uses project_actions.STALE_DAYS_DEFAULT and flags stalled."""
        from datetime import timedelta
        from agent_os.executive.project_actions import STALE_DAYS_DEFAULT

        entry = self._make_registry_entry()
        today_date = date(2026, 10, 5)

        # Project updated STALE_DAYS_DEFAULT + 1 days ago should be flagged stalled.
        stale_date = today_date - timedelta(days=STALE_DAYS_DEFAULT + 1)
        state = self._make_state(
            updated_at=f"{stale_date.isoformat()}T10:00:00Z",
            next_action="Do something",
        )
        items = project_items(lambda: [(entry, state)], today=today_date)
        stalled_items = [i for i in items if i["kind"] == "project_stalled"]
        self.assertEqual(len(stalled_items), 1, "Project older than STALE_DAYS_DEFAULT should be stalled")

        # Project updated exactly STALE_DAYS_DEFAULT days ago should NOT be stalled.
        edge_date = today_date - timedelta(days=STALE_DAYS_DEFAULT)
        state_edge = self._make_state(
            updated_at=f"{edge_date.isoformat()}T10:00:00Z",
            next_action="Do something",
        )
        items_edge = project_items(lambda: [(entry, state_edge)], today=today_date)
        stalled_items_edge = [i for i in items_edge if i["kind"] == "project_stalled"]
        self.assertEqual(len(stalled_items_edge), 0, "Project exactly STALE_DAYS_DEFAULT days old should not be stalled")

    def test_context_has_project_key(self):
        """Every item context has 'project' key with the project id."""
        entry = self._make_registry_entry("test-proj")
        state = self._make_state(project="test-proj")
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        self.assertGreater(len(items), 0)
        for item in items:
            self.assertEqual(item["context"]["project"], "test-proj")

    def test_entries_without_state_file_skipped_by_default_loader(self):
        """_load_projects skips entries without state_file."""
        from agent_os.executive.window.providers_projects import _load_projects

        entries = [{"id": "p1", "state_file": "path/state.json"}, {"id": "p2"}]
        with patch("agent_os.registry.canonical_projects", return_value=entries),                 patch("agent_os.registry.load_state", side_effect=lambda e: {"status": "active", "project": e["id"]}):
            projects = _load_projects()
        self.assertEqual([entry["id"] for entry, _ in projects], ["p1"])

    def test_entries_with_load_exception_skipped_by_default_loader(self):
        """_load_projects silently skips entries whose load_state raises."""
        from agent_os.executive.window.providers_projects import _load_projects

        def load_state(entry):
            if entry["id"] == "p2":
                raise OSError("File not found")
            return {"status": "active", "project": entry["id"]}

        entries = [{"id": "p1", "state_file": "path/state.json"}, {"id": "p2", "state_file": "bad/state.json"}]
        with patch("agent_os.registry.canonical_projects", return_value=entries),                 patch("agent_os.registry.load_state", side_effect=load_state):
            projects = _load_projects()
        self.assertEqual([entry["id"] for entry, _ in projects], ["p1"])

    def test_stalled_why_message_with_age_days(self):
        """Stalled item why message includes age_days when available."""
        entry = self._make_registry_entry()
        state = self._make_state(
            updated_at="2026-09-01T10:00:00Z", next_action="Do it"
        )
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5), stale_days=30)
        stalled_item = [i for i in items if i["kind"] == "project_stalled"][0]
        self.assertIn("34 days", stalled_item["why"])
        self.assertIn("stalled after 30", stalled_item["why"])

    def test_multiple_projects_each_with_multiple_flags(self):
        """Multiple projects with multiple flags each produce correct items."""
        entries = [
            self._make_registry_entry("proj-a", "Project A"),
            self._make_registry_entry("proj-b", "Project B"),
        ]
        states = [
            self._make_state(
                project="proj-a",
                updated_at="2026-08-01T10:00:00Z",
                decisions_needed=["Decision A1", "Decision A2"],
            ),
            self._make_state(
                project="proj-b",
                decisions_needed=["Decision B1"],
            ),
        ]
        load_func = lambda: list(zip(entries, states))
        items = project_items(load_func, today=date(2026, 10, 5), stale_days=30)
        # proj-a: 2 decisions + stalled + no_next_action = 4 items; proj-b: 1 decision + no_next_action = 2 items
        self.assertEqual(len(items), 6)
        proj_a_items = [i for i in items if i["context"]["project"] == "proj-a"]
        proj_b_items = [i for i in items if i["context"]["project"] == "proj-b"]
        self.assertEqual(len(proj_a_items), 4)
        self.assertEqual(len(proj_b_items), 2)


if __name__ == "__main__":
    unittest.main()
