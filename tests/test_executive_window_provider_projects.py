"""Tests for project provider: project queue items from state."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window.providers_projects import project_items


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
        self.assertGreaterEqual(len(items), 2)
        scores = [item["score"] for item in items]
        # Scores should be in descending order within the project items
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1])

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
        """When stale_days=None, uses project_actions.STALE_DAYS_DEFAULT."""
        entry = self._make_registry_entry()
        from agent_os.executive.project_actions import STALE_DAYS_DEFAULT

        state = self._make_state(
            updated_at=f"2026-{10 - (STALE_DAYS_DEFAULT + 1) // 30:02d}-"
            f"{1 + ((10 - 1) * 30 - (STALE_DAYS_DEFAULT + 1) % 30) % 30:02d}T10:00:00Z"
        )
        items = project_items(lambda: [(entry, state)], today=date(2026, 10, 5))
        # Should produce at least a stalled item if old enough
        self.assertGreater(len(items), 0)

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
        from unittest.mock import Mock

        # Mock registry functions
        def mock_canonical():
            return [
                {"id": "p1", "state_file": "path/state.json"},
                {"id": "p2"},  # No state_file
            ]

        def mock_load_state(entry):
            return {"status": "active", "project": entry["id"]}

        # Patch the registry module
        import agent_os.registry

        original_canonical = agent_os.registry.canonical_projects
        original_load_state = agent_os.registry.load_state

        try:
            agent_os.registry.canonical_projects = mock_canonical
            agent_os.registry.load_state = mock_load_state
            projects = _load_projects()
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0][0]["id"], "p1")
        finally:
            agent_os.registry.canonical_projects = original_canonical
            agent_os.registry.load_state = original_load_state

    def test_entries_with_load_exception_skipped_by_default_loader(self):
        """_load_projects silently skips entries whose load_state raises."""
        from agent_os.executive.window.providers_projects import _load_projects

        def mock_canonical():
            return [
                {"id": "p1", "state_file": "path/state.json"},
                {"id": "p2", "state_file": "bad/state.json"},
            ]

        def mock_load_state(entry):
            if entry["id"] == "p2":
                raise OSError("File not found")
            return {"status": "active", "project": entry["id"]}

        import agent_os.registry

        original_canonical = agent_os.registry.canonical_projects
        original_load_state = agent_os.registry.load_state

        try:
            agent_os.registry.canonical_projects = mock_canonical
            agent_os.registry.load_state = mock_load_state
            projects = _load_projects()
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0][0]["id"], "p1")
        finally:
            agent_os.registry.canonical_projects = original_canonical
            agent_os.registry.load_state = original_load_state

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
