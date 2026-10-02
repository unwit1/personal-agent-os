import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

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
        self.assertIn("'/api/confirm'", js, 'JS must call /api/confirm endpoint')

        # Verify variable declaration before use in renderMailCleanup
        const_by_account_idx = js.find('const byAccount = spamFiltered.by_account')
        use_by_account_idx = js.find('byAccount[account]')
        self.assertGreater(const_by_account_idx, -1, 'byAccount must be declared')
        self.assertGreater(use_by_account_idx, -1, 'byAccount must be used')
        self.assertLess(const_by_account_idx, use_by_account_idx,
                       'byAccount declaration must appear before its first use')

        # Verify CSS classes for mail cleanup and filtered display
        self.assertIn('.mail-cleanup-table', html)
        self.assertIn('.mail-cleanup-account', html)
        self.assertIn('.mail-cleanup-filtered', html)
        self.assertIn('.mail-filtered', html)
        self.assertIn('.mail-filtered-counts', html)


if __name__ == '__main__':
    unittest.main()
