"""Tests for the Today ranking, project tab, openings, bridge env and models refresh fixes."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import next_action
from agent_os.executive.window import actions_openings, model_bridge
from agent_os.executive.window.providers_projects import project_items
from agent_os.orchestrator import models


def _qi(qid, kind, source, priority=0, age=0):
    return {
        "id": qid,
        "priority": priority,
        "source": f"window:{source}",
        "window_item": {"id": qid, "kind": kind, "source": source, "age_days": age},
    }


class TestDomainRanking(unittest.TestCase):
    def test_hiring_outranks_project_housekeeping(self):
        items = [
            _qi("qi-hobby", "project_no_next_action", "Project hobby", priority=9, age=90),
            _qi("qi-mail", "mail_thread", "mail", priority=1),
            _qi("qi-app", "applicant_group", "applicant_executive", priority=0),
            _qi("qi-county", "county_openings", "county", priority=0),
        ]
        ids = [i["id"] for i in next_action.rank(items)]
        self.assertEqual(ids, ["qi-app", "qi-county", "qi-mail", "qi-hobby"])

    def test_approvals_between_communications_and_projects(self):
        items = [
            _qi("c", "project_stalled", "Project x"),
            _qi("b", "orchestrator_gate", "Run abc"),
            _qi("a", "mail_review", "mail"),
        ]
        self.assertEqual([i["id"] for i in next_action.rank(items)], ["a", "b", "c"])

    def test_priority_and_age_order_within_a_domain_and_deterministic(self):
        items = [_qi("b", "applicant_group", "x", 1, 1), _qi("a", "applicant_group", "x", 1, 1), _qi("c", "applicant_group", "x", 2, 0)]
        self.assertEqual([i["id"] for i in next_action.rank(items)], ["c", "a", "b"])
        self.assertEqual(next_action.rank(items), next_action.rank(list(reversed(items))))

    def test_ranking_text_mentions_domain(self):
        self.assertIn("hiring", next_action.RANKING)
        self.assertIn("domain weight", next_action.RANKING)


class TestPersonalProjects(unittest.TestCase):
    def test_non_work_classification_goes_to_personal_tab(self):
        def load():
            return [
                ({"id": "lore", "name": "Lore", "classification": "hobby"}, {"project": "lore", "status": "active", "updated_at": "2026-10-15"}),
                ({"id": "ops", "name": "Ops", "classification": "active"}, {"project": "ops", "status": "active", "updated_at": "2026-10-15"}),
            ]

        items = project_items(load_projects=load, today=date(2026, 10, 16), deferral_counts=lambda: {})
        tabs = {i["context"]["project"]: i["tab"] for i in items}
        self.assertEqual(tabs, {"lore": "personal", "ops": "work"})


class TestOpeningsEventScope(unittest.TestCase):
    def test_not_wildcard(self):
        action = actions_openings.REGISTRY._actions["openings.event"]
        self.assertNotEqual(action["applies_to"], "*")
        self.assertEqual(set(action["applies_to"]), {"applicant_group", "county_openings", "openings_console"})


class TestChildEnv(unittest.TestCase):
    def test_session_variables_dropped(self):
        env = {
            "CLAUDE_CODE_SESSION_ID": "s", "CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli",
            "ANTHROPIC_API_KEY": "k", "PATH": "/bin",
        }
        with patch.dict(os.environ, env, clear=True):
            child = model_bridge._child_env()
        self.assertEqual(child, {"PATH": "/bin"})


class TestRefreshMissingProviders(unittest.TestCase):
    def test_returns_none_when_providers_json_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "providers.json"
            with patch("agent_os.capabilities.registry_path", return_value=missing):
                self.assertIsNone(models.refresh(online=True))


if __name__ == "__main__":
    unittest.main()
