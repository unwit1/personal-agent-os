"""Price and benchmark evidence routing."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import model_value  # noqa: E402


class ModelValueTests(unittest.TestCase):
    def test_effective_price_and_missing_fields(self):
        price = {"input": 2, "cached_input": 0.2, "output": 10}
        self.assertEqual(model_value.effective_price(price), 0.58)
        self.assertIsNone(model_value.effective_price({"input": 2, "output": 10}))

    def test_record_evidence_merges_and_deduplicates_source(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory, mock.patch.object(
            model_value, "evidence_path", return_value=Path(directory) / "evidence.json"
        ):
            model_value.record_evidence("gpt-6-sol", price={"input": 2}, source="source")
            entry = model_value.record_evidence(
                "gpt-6-sol", price={"output": 10}, benchmarks={"intelligence_index": 48}, source="source"
            )
            self.assertEqual(entry["price"], {"input": 2, "output": 10})
            self.assertEqual(entry["benchmarks"], {"intelligence_index": 48})
            self.assertEqual(entry["sources"], ["source"])
            self.assertEqual(json.loads((Path(directory) / "evidence.json").read_text())["models"]["gpt-6-sol"], entry)

    def test_resolves_latest_claude_alias(self):
        evidence = {"models": {"claude-opus-5": {}, "claude-opus-5-5": {}}}
        self.assertEqual(model_value.resolve_model("claude-code", "opus", evidence), "claude-opus-5-5")

    def test_tier_costs(self):
        providers = [
            {"id": "claude-code", "models": {"reasoning": "opus", "balanced": "sonnet"}, "costs": {}},
            {"id": "codex", "models": {"reasoning": "gpt-6-sol", "balanced": "gpt-6-sol"}, "costs": {}},
        ]
        evidence = {"models": {
            "claude-opus-5-5": {"price": {"input": 4, "cached_input": .2, "output": 20}, "benchmarks": {"intelligence_index": 58}},
            "claude-sonnet-5": {"price": {"input": 2, "cached_input": .2, "output": 10}},
            "gpt-6-sol": {"price": {"input": 2, "cached_input": .2, "output": 10}, "benchmarks": {"intelligence_index": 48}},
        }}
        result = model_value.tier_costs(providers, evidence)
        self.assertEqual(result["tiers"]["reasoning"]["winner"], "claude-code")
        self.assertEqual(result["tiers"]["balanced"]["status"], "ok")
        self.assertEqual(result["costs"]["claude-code"]["balanced"], .58)
        self.assertEqual(result["costs"]["codex"]["balanced"], .58)
        self.assertEqual(result["tiers"]["balanced"]["winner"], "claude-code")

        evidence["models"]["claude-opus-5-5"]["benchmarks"].pop("intelligence_index")
        result = model_value.tier_costs(providers, evidence)
        self.assertEqual(result["tiers"]["reasoning"]["status"], "needs_evidence")
        self.assertNotIn("reasoning", result["costs"].get("claude-code", {}))
        self.assertNotIn("reasoning", result["costs"].get("codex", {}))


if __name__ == "__main__":
    unittest.main()
