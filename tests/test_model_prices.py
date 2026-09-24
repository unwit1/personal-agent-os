import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.model_prices import fetch_prices, parse_anthropic, parse_openai


ROOT = Path(__file__).resolve().parent


class ModelPricesTests(unittest.TestCase):
    def test_openai_fixture(self):
        markdown = (ROOT / "fixtures" / "pricing" / "openai.md").read_text(encoding="utf-8")
        prices = parse_openai(markdown)
        self.assertEqual(prices["gpt-6-sol"], {"input": 2.0, "cached_input": 0.2, "output": 10.0})
        self.assertEqual(prices["gpt-6-luna"], {"input": 0.1, "cached_input": 0.01, "output": 0.5})
        self.assertEqual(prices["gpt-5.6-terra"]["output"], 12.0)

    def test_anthropic_fixture(self):
        markdown = (ROOT / "fixtures" / "pricing" / "anthropic.md").read_text(encoding="utf-8")
        prices = parse_anthropic(markdown)
        self.assertEqual(prices["claude-sonnet-5"], {"input": 2.0, "cached_input": 0.2, "output": 10.0})
        self.assertEqual(prices["claude-opus-5-5"], {"input": 4.0, "cached_input": 0.2, "output": 20.0})
        self.assertEqual(prices["claude-haiku-4-5"], {"input": 1.0, "cached_input": 0.1, "output": 5.0})
        self.assertFalse(any("mythos" in model for model in prices))

    def test_fetch_prices_records_failures(self):
        class BrokenOpener:
            def open(self, request, timeout):
                raise OSError("offline")

        result = fetch_prices(BrokenOpener().open)
        self.assertEqual(len(result["checks"]), 2)
        self.assertTrue(all(check["ok"] is False for check in result["checks"]))
        self.assertEqual(result["prices"], {})


if __name__ == "__main__":
    unittest.main()
