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
        self.assertEqual(js.count("'/api/send'"), 1)
        self.assertIn("'/api/send/accounts'", js)
        self.assertIn('from_account', js)
        self.assertIn("'/api/dismiss'", js)
        self.assertRegex(
            js,
            r"sendBtn\.addEventListener\('click',\s*\(\)\s*=>\s*\{[\s\S]*?'/api/send'",
        )
        before_handler = js.split("sendBtn.addEventListener('click'")[0]
        self.assertNotIn("'/api/send'", before_handler)

    def test_applicant_review_uses_server_shape(self) -> None:
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        js = (gui_dir / 'executive.js').read_text(encoding='utf-8')
        self.assertNotIn('applicant_id', js)
        self.assertIn('applicant_ref: applicant.applicant_ref', js)
        self.assertIn('review.available_decisions', js)
        self.assertIn('applicant.recommendation', js)
        self.assertNotIn('applicant.suggestion', js)
        for label in ('Score', 'Summary', 'Strengths', 'Concerns', 'AI suggestion - you decide'):
            self.assertIn(label, js)

    def test_confirm_card_is_plain_english_and_accessible(self) -> None:
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        js = (gui_dir / 'executive.js').read_text(encoding='utf-8')
        html = (gui_dir / 'executive.html').read_text(encoding='utf-8')
        self.assertIn("'alertdialog'", js)
        self.assertIn('aria-labelledby', js)
        self.assertIn('confirmBtn.focus()', js)
        self.assertIn("'Keep as is'", js)
        self.assertIn("'Details'", js)
        self.assertNotIn("'Preview: '", js)
        self.assertIn("'Decline ' + name + where + '?'", js)
        self.assertIn('#8a5a12', html)
        self.assertNotIn('position: fixed', html.split('.pending-previews {')[1].split('}')[0])

    def test_item_actions_and_errors(self) -> None:
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        js = (gui_dir / 'executive.js').read_text(encoding='utf-8')
        html = (gui_dir / 'executive.html').read_text(encoding='utf-8')
        self.assertIn("option.action_id === 'item.dismiss'", js)
        self.assertIn('optionShownOnCard', js)
        self.assertIn('id="error-banner"', html)
        self.assertIn('role="alert"', html)
        self.assertIn("'Retry'", js)
        self.assertNotIn('provider-errors', html + js)
        self.assertNotIn("'Source: '", js)
        self.assertIn("'Priority ' + item.rank.position + ' of ' + item.rank.of", js)
        self.assertIn('(asks before doing)', js)

    def test_first_screen_and_labels(self) -> None:
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        html = (gui_dir / 'executive.html').read_text(encoding='utf-8')
        css = (gui_dir / 'style.css').read_text(encoding='utf-8')
        self.assertIn('<h1>Today</h1>', html)
        self.assertIn('id="today-count"', html)
        for chip in ('Find top applicants', 'Write a job description', 'What needs me today?', 'Start a coding task'):
            self.assertIn(chip, html)
        self.assertIn("Ask me anything - e.g. 'Draft a job description for an Executive Assistant'", html)
        self.assertIn('aria-label="Ask me anything"', html)
        self.assertIn('Quick notes', html)
        self.assertIn('Just one thing', html)
        self.assertNotIn('Brain dump', html)
        self.assertIn('Working on it... this can take up to a minute', html)
        self.assertIn('align-content: start', css)
        self.assertIn('@media (max-width: 1024px)', css)

    def test_executive_js_rank_display(self) -> None:
        """Test that rank display is implemented and positioned after why."""
        gui_dir = Path(__file__).resolve().parents[1] / 'gui'
        js_file = gui_dir / 'executive.js'
        js_content = js_file.read_text(encoding='utf-8')

        self.assertIn('item-rank', js_content, "JS does not contain 'item-rank'")
        self.assertIn('item.rank.position', js_content, "JS does not contain 'item.rank.position'")

        why_pos = js_content.find('item-why')
        rank_pos = js_content.find('item-rank')
        self.assertGreater(why_pos, -1, "'item-why' not found in JS")
        self.assertGreater(rank_pos, -1, "'item-rank' not found in JS")
        self.assertGreater(rank_pos, why_pos, "'item-rank' should appear after 'item-why' in the file")


if __name__ == '__main__':
    unittest.main()
