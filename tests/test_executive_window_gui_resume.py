import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

GUI = Path(__file__).resolve().parents[1] / 'gui'


class ExecutiveWindowResumeTests(unittest.TestCase):
    def test_resume_result_is_rendered(self):
        js = (GUI / 'executive.js').read_text(encoding='utf-8')
        for needle in ('project.resume', 'renderResume', 'where_you_left_off', 'open_loops', 'next_action_source'):
            self.assertIn(needle, js)
        self.assertNotIn('auto-confirm', js.lower())


if __name__ == '__main__':
    unittest.main()
