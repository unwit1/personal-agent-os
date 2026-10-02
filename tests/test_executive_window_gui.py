import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class ExecutiveWindowGUITests(unittest.TestCase):
    """Tests for the Agent OS Executive Window GUI."""

    def test_executive_window_files_exist(self) -> None:
        """Test that executive window files exist."""
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        self.assertTrue((gui_dir / 'executive.html').exists(), "gui/executive.html does not exist")
        self.assertTrue((gui_dir / 'executive.js').exists(), "gui/executive.js does not exist")

    def test_executive_html_structure(self) -> None:
        """Test HTML structure and required elements."""
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        html_file = gui_dir / 'executive.html'
        html_content = html_file.read_text(encoding='utf-8')

        self.assertIn('style.css', html_content, "HTML does not link style.css")
        self.assertIn('executive.js', html_content, "HTML does not link executive.js")
        self.assertIn('Work', html_content, "HTML does not contain Work tab")
        self.assertIn('Personal', html_content, "HTML does not contain Personal tab")
        self.assertIn('{{TOKEN}}', html_content, "HTML does not contain {{TOKEN}} placeholder")

    def test_executive_js_apis(self) -> None:
        """Test that JS contains required API references and headers."""
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        js_file = gui_dir / 'executive.js'
        js_content = js_file.read_text(encoding='utf-8')

        self.assertIn('/api/items', js_content, "JS does not reference /api/items")
        self.assertIn('/api/option', js_content, "JS does not reference /api/option")
        self.assertIn('/api/chat', js_content, "JS does not reference /api/chat")
        self.assertIn('/api/pending', js_content, "JS does not reference /api/pending")
        self.assertIn('/api/confirm', js_content, "JS does not reference /api/confirm")
        self.assertIn('/api/dismiss', js_content, "JS does not reference /api/dismiss")
        self.assertIn('X-Agent-OS-Token', js_content, "JS does not use X-Agent-OS-Token header")

        # Ensure no auto-confirmation
        self.assertNotIn('auto-confirm', js_content.lower(), "JS should not auto-confirm actions")
        self.assertNotIn('autoconfirm', js_content.lower(), "JS should not auto-confirm actions")

    def test_executive_js_compose_and_review(self) -> None:
        """Compose panel, county openings and review wiring; Send is never automatic."""
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        js = (gui_dir / 'executive.js').read_text(encoding='utf-8')

        for needle in ('/api/send', 'compose-panel', 'county_openings', 'applicant.review', 'NOT SENT', '/api/act'):
            self.assertIn(needle, js, f"JS does not contain {needle}")

        # /api/send is called exactly once, directly inside the Send click handler.
        self.assertEqual(js.count('/api/send'), 1)
        self.assertRegex(
            js,
            r"sendBtn\.addEventListener\('click',\s*\(\)\s*=>\s*\{[\s\S]*?'/api/send'",
        )
        before_handler = js.split("sendBtn.addEventListener('click'")[0]
        self.assertNotIn('/api/send', before_handler)


if __name__ == '__main__':
    unittest.main()
