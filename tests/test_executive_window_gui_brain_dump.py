import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

GUI = Path(__file__).resolve().parents[1] / 'gui'


class ExecutiveWindowBrainDumpTests(unittest.TestCase):
    def test_brain_dump_capture_and_clarification_ui(self):
        html = (GUI / 'executive.html').read_text(encoding='utf-8')
        js = (GUI / 'executive.js').read_text(encoding='utf-8')

        self.assertIn('id="brain-dump-input"', html)
        self.assertIn('id="brain-dump-send"', html)
        for needle in ('/api/brain-dump', 'brain_dump.clarify', 'brain_dump.stage_candidate', 'brain_dump_clarification'):
            self.assertIn(needle, js)
        self.assertNotIn('auto-confirm', js.lower())
        self.assertIn("getElementById('brain-dump-send').addEventListener('click', handleBrainDumpSend)", js)
        self.assertIn("option.action_id === 'brain_dump.stage_candidate'", js)
        self.assertIn('runAction(item, option.action_id, {})', js)
        self.assertEqual(js.count("runAction(item, 'brain_dump.clarify'"), 2)


if __name__ == '__main__':
    unittest.main()
