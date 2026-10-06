import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import tempfile
import unittest

from agent_os.executive.window.gap_store import GapStore


class GapStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.store = GapStore(self.home)

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_skips_invalid_and_duplicate_ids_and_falls_back_tab(self):
        self.assertEqual(self.store.add([
            None,
            {'id': '', 'question': 'empty id'},
            {'id': 'blank-question', 'question': '  '},
            {'id': 'a', 'question': 'Question A'},
            {'id': 'a', 'question': 'Repeated'},
        ], tab='other'), ['a'])
        self.assertEqual(self.store.get('a')['tab'], 'personal')
        self.assertEqual(self.store.add([{'id': 'a', 'question': 'Duplicate'}]), [])
        self.store.add([{'id': 'w', 'question': 'Work question'}], tab='work')
        self.assertEqual(self.store.get('w')['tab'], 'work')

    def test_gaps_sort_and_filter_and_mark_answered(self):
        self.store.add([
            {'id': 'b', 'question': 'B'},
            {'id': 'a', 'question': 'A'},
        ])
        data = self.store._load()
        data['gaps']['b']['added_at'] = '2026-01-02'
        data['gaps']['a']['added_at'] = '2026-01-01'
        self.store._save(data)
        record = self.store.mark_answered('a', 'Answer', {
            'created': [{'id': 'candidate-1'}],
            'duplicates': [{'id': 'candidate-2'}],
        })
        self.assertEqual(record['candidate_ids'], ['candidate-1', 'candidate-2'])
        self.assertEqual(record['answer'], 'Answer')
        self.assertEqual(self.store.answered_ids(), {'a'})
        self.assertEqual([gap['id'] for gap in self.store.gaps()], ['b'])
        self.assertEqual([gap['id'] for gap in self.store.gaps(None)], ['a', 'b'])
        self.assertEqual([gap['id'] for gap in self.store.gaps('answered')], ['a'])

    def test_unknown_gap_raises_key_error(self):
        with self.assertRaisesRegex(KeyError, 'unknown knowledge gap: missing'):
            self.store.get('missing')
        with self.assertRaisesRegex(KeyError, 'unknown knowledge gap: missing'):
            self.store.mark_answered('missing', 'Answer', {})


if __name__ == '__main__':
    unittest.main()
