from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import main


class DocumentCacheCliTests(unittest.TestCase):
    def test_document_cache_status_calls_stats_and_prints_json(self) -> None:
        mock_stats_result = {"entries": 3, "bytes": 10}
        with patch("agent_os.cli.DocumentCache") as mock_doc_cache_class:
            mock_instance = MagicMock()
            mock_doc_cache_class.return_value = mock_instance
            mock_instance.stats.return_value = mock_stats_result

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["document-cache-status"])

            self.assertIn(result, (0, None))
            mock_doc_cache_class.assert_called_once()
            mock_instance.stats.assert_called_once()

            printed_json = json.loads(output.getvalue())
            self.assertEqual(printed_json, mock_stats_result)

    def test_document_cache_clear_calls_clear_and_prints_json(self) -> None:
        mock_clear_result = {"cleared": True}
        with patch("agent_os.cli.DocumentCache") as mock_doc_cache_class:
            mock_instance = MagicMock()
            mock_doc_cache_class.return_value = mock_instance
            mock_instance.clear.return_value = mock_clear_result

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["document-cache-clear"])

            self.assertIn(result, (0, None))
            mock_doc_cache_class.assert_called_once()
            mock_instance.clear.assert_called_once()

            printed_json = json.loads(output.getvalue())
            self.assertEqual(printed_json, mock_clear_result)

    def test_document_cache_prune_calls_with_defaults(self) -> None:
        mock_prune_result = {"pruned": 5}
        with patch("agent_os.cli.DocumentCache") as mock_doc_cache_class:
            mock_instance = MagicMock()
            mock_doc_cache_class.return_value = mock_instance
            mock_instance.prune.return_value = mock_prune_result

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["document-cache-prune"])

            self.assertIn(result, (0, None))
            mock_doc_cache_class.assert_called_once()
            mock_instance.prune.assert_called_once_with(536870912, 90)

            printed_json = json.loads(output.getvalue())
            self.assertEqual(printed_json, mock_prune_result)

    def test_document_cache_prune_with_custom_arguments(self) -> None:
        mock_prune_result = {"pruned": 2}
        with patch("agent_os.cli.DocumentCache") as mock_doc_cache_class:
            mock_instance = MagicMock()
            mock_doc_cache_class.return_value = mock_instance
            mock_instance.prune.return_value = mock_prune_result

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["document-cache-prune", "--max-bytes", "1024", "--max-age-days", "7"])

            self.assertIn(result, (0, None))
            mock_doc_cache_class.assert_called_once()
            mock_instance.prune.assert_called_once_with(1024, 7)

            printed_json = json.loads(output.getvalue())
            self.assertEqual(printed_json, mock_prune_result)


if __name__ == "__main__":
    unittest.main()
