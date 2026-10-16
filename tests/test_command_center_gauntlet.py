"""Regression tests for the command-center usability gauntlet (browser-driven findings)."""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window.registry import Registry
from agent_os.executive.window.rescue_view import rescue_view
from agent_os.executive.window.server import _captured_message
from agent_os.orchestrator.simple import _short

GUI = Path(__file__).resolve().parents[1] / "gui"


class CaptureMessageTests(unittest.TestCase):
    def test_wording(self):
        self.assertEqual(_captured_message(1, 0, 0), "Saved 1 note.")
        self.assertEqual(_captured_message(3, 0, 0), "Saved 3 notes.")
        self.assertEqual(_captured_message(2, 1, 0), "Saved 2 notes. 1 still needs a project.")
        self.assertEqual(_captured_message(2, 2, 1), "Saved 2 notes. 2 still need a project. Skipped 1 you already had.")
        self.assertEqual(_captured_message(0, 0, 1), "You already have that note.")
        self.assertEqual(_captured_message(0, 0, 3), "You already have those 3 notes.")


class RescueCountTests(unittest.TestCase):
    def registry(self, count):
        registry = Registry()
        registry.register_provider("fixture", lambda: [
            {"id": f"w{n}", "tab": "work", "kind": "fixture", "title": f"Item {n}", "why": "x", "source": "fixture"}
            for n in range(count)
        ])
        return registry

    def test_others_waiting_matches_the_today_list(self):
        for count in (1, 2, 5):
            view = rescue_view(self.registry(count), projects=[], today=date(2026, 1, 1))
            queue = self.registry(count).queue(None)["queue_items"]
            self.assertEqual(view["suppressed"], len(queue) - 1, count)

    def test_projects_are_not_counted_twice(self):
        projects = [{"project": f"p{n}", "status": "active", "next_action": f"Do {n}", "flags": [], "age_days": n} for n in range(4)]
        view = rescue_view(self.registry(3), projects=projects, today=date(2026, 1, 1))
        self.assertLessEqual(view["suppressed"], 3)


class ShortTitleTests(unittest.TestCase):
    def test_cuts_at_a_word_and_says_so(self):
        text = "Give the assistant tiered access to the user's computer (Windows primary, must also work on Linux)"
        out = _short(text, 60)
        self.assertTrue(out.endswith("…"))
        self.assertLessEqual(len(out), 61)
        self.assertFalse(out[:-1].endswith(("(", ",", " ")))
        self.assertEqual(_short("short goal", 60), "short goal")
        self.assertEqual(_short("a  b\n c", 60), "a b c")


class GuiSourceTests(unittest.TestCase):
    def test_layout_cannot_be_widened_by_long_text(self):
        html = (GUI / "executive.html").read_text(encoding="utf-8")
        self.assertIn("minmax(0, 1fr)", html)
        self.assertNotIn("grid-template-columns: 1fr 1fr", html)
        self.assertIn("overflow-wrap: anywhere", html)
        self.assertIn('rel="icon"', html)

    def test_keyboard_and_focus_behaviour(self):
        js = (GUI / "executive.js").read_text(encoding="utf-8")
        self.assertIn("event.key === 'Escape'", js)
        self.assertIn("function returnFocus", js)
        self.assertGreaterEqual(js.count("isComposing"), 2)
        self.assertNotIn("addEventListener('keypress'", js)

    def test_disabled_buttons_explain_themselves(self):
        js = (GUI / "executive.js").read_text(encoding="utf-8")
        self.assertIn("function needsText", js)
        self.assertIn("This project's folder isn't on this computer", js)
        self.assertIn("function friendlyTime", js)
        self.assertNotIn("project.handoff.created_at || ''", js)

    def test_small_screens_and_a_dead_server_are_handled(self):
        js = (GUI / "executive.js").read_text(encoding="utf-8")
        css = (GUI / "style.css").read_text(encoding="utf-8")
        self.assertIn("Can't reach the Command Center", js)
        self.assertIn("error instanceof TypeError", js)
        self.assertIn("minmax(min(290px, 100%), 1fr)", css)
        self.assertIn("input, textarea, select { max-width: 100%; min-width: 0;", css)

    def test_empty_chat_has_a_hint(self):
        css = (GUI / "style.css").read_text(encoding="utf-8")
        self.assertIn("#chat-log:empty::before", css)


if __name__ == "__main__":
    unittest.main()
