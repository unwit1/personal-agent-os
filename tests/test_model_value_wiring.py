"""Integration coverage for pricing evidence and registry cost wiring."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import capabilities  # noqa: E402
from agent_os.orchestrator import model_value, models  # noqa: E402
from agent_os.orchestrator.model_prices import PRICE_PAGES  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402


class ModelValueWiringTests(unittest.TestCase):
    def test_refresh_records_prices_and_updates_registry_costs(self):
        root = Path(__file__).resolve().parent
        fixture_paths = {
            PRICE_PAGES[0]["url"]: root / "fixtures" / "pricing" / "anthropic.md",
            PRICE_PAGES[1]["url"]: root / "fixtures" / "pricing" / "openai.md",
        }

        class Response:
            def __init__(self, body: str):
                self.body = body.encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self, _limit):
                return self.body

        def opener(request, timeout):
            url = request.full_url
            path = fixture_paths.get(url)
            return Response(path.read_text(encoding="utf-8") if path else "")

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            registry_file = home / "providers.json"
            registry_file.write_text(json.dumps({"providers": [
                {"id": "claude-code", "models": {"reasoning": "opus"}, "costs": {"reasoning": 8.0}},
                {"id": "codex", "models": {"reasoning": "gpt-6-sol"}, "costs": {"reasoning": 9.0}},
            ]}), encoding="utf-8")
            evidence_file = home / "models" / "evidence.json"
            evidence_file.parent.mkdir(parents=True)
            evidence_file.write_text(json.dumps({"models": {
                "claude-opus-5-5": {"benchmarks": {"intelligence_index": 60}},
                "gpt-6-sol": {"benchmarks": {"intelligence_index": 48}},
            }}), encoding="utf-8")
            registry = ProviderRegistry(path=registry_file, discover=False)
            with mock.patch.object(models, "orchestrator_home", return_value=home), \
                    mock.patch.object(model_value, "orchestrator_home", return_value=home), \
                    mock.patch.object(capabilities, "registry_path", return_value=registry_file):
                result = models.refresh(online=True, opener=opener, registry=registry)

            evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
            self.assertEqual(evidence["models"]["gpt-6-sol"]["price"], {
                "input": 2.0, "cached_input": 0.2, "output": 10.0,
            })
            self.assertIn("value", result)
            self.assertEqual(result["value"]["reasoning"]["status"], "ok")
            updated = json.loads(registry_file.read_text(encoding="utf-8"))
            self.assertNotEqual(updated["providers"][1]["costs"]["reasoning"], 9.0)
            self.assertTrue(registry_file.with_name(registry_file.name + ".bak-value").exists())


if __name__ == "__main__":
    unittest.main()
