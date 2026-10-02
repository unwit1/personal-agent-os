import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest
import re

GUI = Path(__file__).resolve().parents[1] / 'gui'


class MailCleanupGuiTests(unittest.TestCase):
    def test_mail_cleanup_feature_integration(self):
        js = (GUI / 'executive.js').read_text(encoding='utf-8')
        html = (GUI / 'executive.html').read_text(encoding='utf-8')

        # Verify item.kind checks for both mail_cleanup and mail_filtered
        self.assertIn("item.kind === 'mail_cleanup'", js)
        self.assertIn("item.kind === 'mail_filtered'", js)

        # Verify action_id pattern with params for mail.organize_apply
        self.assertRegex(js, r"action_id:\s*'mail\.organize_apply'")
        self.assertRegex(js, r"params:\s*\{\s*account:\s*account,\s*category:\s*category\s*\}")

        # Verify /api/act and /api/confirm endpoints
        self.assertIn("'/api/act'", js)
        self.assertIn("'/api/confirm'", js)

        # Verify API confirm flow
        self.assertIn('response.confirm_token', js)

        # Verify mail cleanup UI references
        self.assertIn('No plan yet', js)
        self.assertIn('.categories', js)

        # Verify CSS for mail cleanup and filtered display
        self.assertIn('.mail-cleanup-table', html)
        self.assertIn('.mail-cleanup-account', html)
        self.assertIn('.mail-cleanup-filtered', html)
        self.assertIn('.mail-filtered', html)
        self.assertIn('.mail-filtered-counts', html)


if __name__ == '__main__':
    unittest.main()
