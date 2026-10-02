import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import re
import unittest

GUI = Path(__file__).resolve().parents[1] / 'gui'


class MailCleanupGuiTests(unittest.TestCase):
    def test_mail_cleanup_feature_integration(self):
        js = (GUI / 'executive.js').read_text(encoding='utf-8')
        html = (GUI / 'executive.html').read_text(encoding='utf-8')

        # Required string references for mail_cleanup feature
        self.assertIn('mail_cleanup', js, 'JS must reference mail_cleanup kind')
        self.assertIn('mail_filtered', js, 'JS must reference mail_filtered kind')
        self.assertIn('mail.organize_apply', js, 'JS must reference mail.organize_apply action')
        # The per-category apply button posts the action with its account and
        # category to /api/act, which returns a preview for the operator to confirm.
        apply_fn = js[js.index('function handleMailOrganizeApply'):]
        apply_fn = apply_fn[:re.search(r'\n  \}\r?\n', apply_fn).start()]
        self.assertIn("'/api/act'", apply_fn)
        self.assertIn("action_id: 'mail.organize_apply'", apply_fn)
        self.assertIn('params: { account: account, category: category }', apply_fn)
        self.assertIn('showPreview(', apply_fn)
        self.assertIn("'No plan yet'", js)

        # Verify CSS classes for mail cleanup and filtered display
        self.assertIn('.mail-cleanup-table', html)
        self.assertIn('.mail-cleanup-account', html)
        self.assertIn('.mail-cleanup-filtered', html)
        self.assertIn('.mail-filtered', html)
        self.assertIn('.mail-filtered-counts', html)
        self.assertIn('.muted {', html)


if __name__ == '__main__':
    unittest.main()
