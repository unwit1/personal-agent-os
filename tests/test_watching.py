import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from agent_os.watching import add_target, list_targets


class TestWatching(unittest.TestCase):
    def test_watch_target_deduplicates_and_merges(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            with patch("agent_os.watching.WATCH_DIR", tmp_path), \
                 patch("agent_os.watching.WATCH_INDEX", tmp_path / "index.json"):
                first = add_target({"source_id": "youtube:creator:abc", "title": "Creator", "target_type": "creator", "search_queries": ["Creator new video"]})
                second = add_target({"source_id": "youtube:creator:abc", "title": "Creator", "target_type": "creator", "related_topics": ["skyrim"]})
                self.assertEqual(first["watch_id"], second["watch_id"])
                targets = list_targets()
                self.assertEqual(len(targets), 1)
                self.assertEqual(targets[0]["search_queries"], ["Creator new video"])
                self.assertEqual(targets[0]["related_topics"], ["skyrim"])
