"""Subscription model research (model_research.py). HTTP is faked."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import model_research  # noqa: E402


def entry(model_id: str, *, ctx: int = 262144, price: float = 0.1, created: int = 1_790_000_000, category: str = "More", **caps) -> dict:
    return {"id": model_id, "context_length": ctx, "created": created, "category": category, "open_weights": True,
            "pricing": {"prompt": price}, "capabilities": {"structured_output": True, "reasoning": True, "tool_calling": True, **caps}}


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FitTests(unittest.TestCase):
    def test_measured_planning_outranks_priors_and_roleplay_is_excluded(self) -> None:
        models = [entry("prior-strong"), entry("measured"), entry("rp", category="Roleplay/storytelling models"),
                  entry("plain-abliterated", structured_output=False)]
        priors = {"models": {"prior-strong": {"aa_index": 50}}}
        reports = [{"model": "measured", "cases": [{"passed": True, "valid": True, "usage": {"model_resolved": "measured"}}] * 12}]
        fit = model_research.build_fit(models, priors=priors, reports=reports, observations=[])
        planning = [row["id"] for row in fit["families"]["planning"]["ranked"]]
        self.assertEqual(planning[:2], ["measured", "prior-strong"])
        self.assertNotIn("rp", planning)
        self.assertNotIn("plain-abliterated", planning)  # no structured output
        self.assertIn("plain-abliterated", [row["id"] for row in fit["families"]["uncensored_writing"]["ranked"]])
        self.assertEqual(fit["catalog"]["uncensored_or_abliterated"], ["plain-abliterated"])
        self.assertEqual(fit["families"]["planning"]["ranked"][0]["measured"]["planning"]["cases"], 12)

    def test_family_filters(self) -> None:
        models = [entry("long", ctx=1_048_576, price=0.5), entry("cheap", price=0.05), entry("eyes", vision=True)]
        fit = model_research.build_fit(models, priors={}, reports=[], observations=[])
        self.assertEqual([row["id"] for row in fit["families"]["long_context"]["ranked"]], ["long"])
        self.assertEqual([row["id"] for row in fit["families"]["triage"]["ranked"]], ["cheap", "eyes"])
        self.assertEqual([row["id"] for row in fit["families"]["vision"]["ranked"]], ["eyes"])

    def test_allowance_summary(self) -> None:
        usage = {"limits": {"weeklyInputTokens": 60_000_000, "dailyImages": 100}, "allowOverage": False,
                 "weeklyInputTokens": {"used": 10, "remaining": 59_999_990, "resetAt": 1_792_368_000_000}, "routing": {"paidOverageEnabled": False}}
        summary = model_research._allowance(usage)
        self.assertEqual((summary["weekly_input_units"], summary["used"], summary["overage_enabled"]), (60_000_000, 10, False))
        self.assertEqual(summary["resets_at"], "2026-10-19T00:00:00+00:00")


class MultiplierTests(unittest.TestCase):
    def measure(self, before: int, after: int, prompt: int) -> dict:
        reads = iter([before, after])

        def opener(request, timeout=0):
            if request.full_url.endswith("/usage"):
                return Response(json.dumps({"weeklyInputTokens": {"used": next(reads)}}).encode())
            return Response(json.dumps({"usage": {"prompt_tokens": prompt}}).encode())

        return model_research.measure_multiplier("m", key="k", opener=opener, sleep=lambda s: None)

    def test_one_and_two_x(self) -> None:
        self.assertEqual(self.measure(100, 325, 225)["multiplier"], 1)
        self.assertEqual(self.measure(100, 550, 225)["multiplier"], 2)

    def test_concurrent_use_is_noisy(self) -> None:
        reading = self.measure(100, 3500, 230)
        self.assertTrue(reading["noisy"])
        self.assertIsNone(reading["multiplier"])


class ResearchTests(unittest.TestCase):
    def test_writes_fit_and_keeps_earlier_multipliers(self) -> None:
        def opener(request, timeout=0):
            if "/models" in request.full_url:
                return Response(json.dumps({"data": [entry("a")]}).encode())
            return Response(json.dumps({"limits": {"weeklyInputTokens": 60}, "weeklyInputTokens": {"used": 1}}).encode())

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "nanogpt-fit.json").write_text(json.dumps({"multipliers": [{"model": "a", "multiplier": 2}]}), encoding="utf-8")
            fit = model_research.research(directory=Path(tmp), opener=opener, key="k", reports=[], observations=[])
            stored = json.loads((Path(tmp) / "nanogpt-fit.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["multipliers"], [{"model": "a", "multiplier": 2}])
        self.assertEqual(fit["catalog"]["models"], 1)


if __name__ == "__main__":
    unittest.main()
