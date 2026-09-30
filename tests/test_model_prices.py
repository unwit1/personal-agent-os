import json
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
        from agent_os.orchestrator.model_prices import PRICE_PAGES

        self.assertEqual(len(result["checks"]), len(PRICE_PAGES))
        self.assertTrue(all(check["ok"] is False for check in result["checks"]))
        self.assertEqual(result["prices"], {})


class OpenRouterPriceTests(unittest.TestCase):
    def test_parses_per_token_prices_and_skips_variants_and_routers(self) -> None:
        from agent_os.orchestrator import model_prices

        payload = json.dumps({"data": [
            {"id": "qwen/qwen3-32b", "pricing": {"prompt": "0.00000008", "completion": "0.00000028"}},
            {"id": "deepseek/v4", "pricing": {"prompt": "0.0000002", "completion": "0.0000008", "input_cache_read": "0.00000002"}},
            {"id": "qwen/qwen3-32b:free", "pricing": {"prompt": "0", "completion": "0"}},
            {"id": "openrouter/auto", "pricing": {"prompt": "-1", "completion": "-1"}},
            {"id": "broken/model", "pricing": {}},
        ]})
        parsed = model_prices.parse_openrouter(payload)
        self.assertEqual(parsed["qwen/qwen3-32b"], {"input": 0.08, "cached_input": 0.08, "output": 0.28})
        self.assertEqual(parsed["deepseek/v4"]["cached_input"], 0.02)
        self.assertEqual(sorted(parsed), ["deepseek/v4", "qwen/qwen3-32b"])
        self.assertEqual(model_prices.parse_openrouter("not json"), {})


if __name__ == "__main__":
    unittest.main()
