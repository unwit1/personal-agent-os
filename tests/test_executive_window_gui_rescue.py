import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

GUI = Path(__file__).resolve().parents[1] / 'gui'


class ExecutiveWindowRescueTests(unittest.TestCase):
    def test_rescue_view_wiring(self):
        html = (GUI / 'executive.html').read_text(encoding='utf-8')
        js = (GUI / 'executive.js').read_text(encoding='utf-8')

        self.assertIn('id="rescue-toggle"', html)
        self.assertIn('id="rescue-panel"', html)
        for needle in ('/api/rescue', 'rescueMode', 'renderRescue', 'item_id', 'suppressed'):
            self.assertIn(needle, js)
        self.assertNotIn('auto-confirm', js.lower())


if __name__ == '__main__':
    unittest.main()
