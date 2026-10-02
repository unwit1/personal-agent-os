import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest

GUI = Path(__file__).resolve().parents[1] / 'gui'


class MailCleanupGuiTests(unittest.TestCase):
    def test_js_references(self):
        js = (GUI / 'executive.js').read_text(encoding='utf-8')
        for needle in ('mail_cleanup', 'mail.organize_apply', 'mail_filtered', '/api/confirm', 'No plan yet'):
            self.assertIn(needle, js)

    def test_api_act_endpoint(self):
        js = (GUI / 'executive.js').read_text(encoding='utf-8')
        self.assertIn("'/api/act'", js)
        # Verify handleMailOrganizeApply uses /api/act
        self.assertIn("apiCall('POST', '/api/act', payload)", js)

    def test_confirm_token_handling(self):
        js = (GUI / 'executive.js').read_text(encoding='utf-8')
        self.assertIn('response.confirm_token', js)

    def test_categories_reference(self):
        js = (GUI / 'executive.js').read_text(encoding='utf-8')
        self.assertIn('.categories', js)

    def test_css_present(self):
        html = (GUI / 'executive.html').read_text(encoding='utf-8')
        self.assertIn('.mail-cleanup-table', html)


if __name__ == '__main__':
    unittest.main()
