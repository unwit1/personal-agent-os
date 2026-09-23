"""Model catalog: sources, notices, proposals, applying them, and the
registry's per-tier overrides. No network (a fake opener) and no model calls."""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import models  # noqa: E402
from agent_os.orchestrator.ledger import Ledger  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402
from agent_os.orchestrator.usage import normalized  # noqa: E402

CLAUDE_PAGE = "Models: claude-sonnet-5, claude-opus-5-5, claude-haiku-4-5-20251001 and claude-fable-5-1."
OPENAI_PAGE = "Pick gpt-6-luna or gpt-6-sol; gpt-6-astra for the hardest work."


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def opener_for(pages: dict[str, str | Exception]):
    def opener(request, timeout=None):
        page = pages.get(request.full_url, "")
        if isinstance(page, Exception):
            raise page
        return FakeResponse(page.encode("utf-8"))

    return opener


def codex_cache(path: Path, extra: list[dict] | None = None) -> Path:
    models_ = [
        {"slug": "gpt-6-astra", "visibility": "list", "priority": 1, "description": "Frontier intelligence for the most demanding work."},
        {"slug": "gpt-6-sol", "visibility": "list", "priority": 2, "description": "Workhorse model for coding and everyday work."},
        {"slug": "gpt-6-luna", "visibility": "list", "priority": 3, "description": "Fast and affordable model for easier tasks."},
        {"slug": "gpt-5.6-terra", "visibility": "list", "priority": 7, "description": "Older balanced model for straightforward work."},
        {"slug": "gpt-reserve", "visibility": "hide", "priority": 3, "description": "Fast and affordable agentic coding model."},
        *(extra or []),
    ]
    path.write_text(json.dumps({"fetched_at": "2026-09-23T00:00:00Z", "models": models_}), encoding="utf-8")
    return path


def registry() -> ProviderRegistry:
    return ProviderRegistry(providers=[
        {"id": "claude-code", "adapter": "claude_code", "models": {"fast": "haiku", "balanced": "sonnet", "reasoning": "opus", "frontier": "fable"}},
        {"id": "codex", "adapter": "codex_cli", "models": {"fast": "gpt-6-luna", "balanced": "gpt-5.6-terra", "reasoning": "gpt-6-sol", "frontier": "gpt-6-astra"}},
    ], discover=False)


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="agent-os-models-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = mock.patch.dict(os.environ, {"AGENT_OS_ORCHESTRATOR_HOME": str(self.tmp / "home")})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cache = codex_cache(self.tmp / "models_cache.json")
        self.pages = {source["url"]: (CLAUDE_PAGE if source["provider"] == "claude-code" else OPENAI_PAGE) for source in models.MODEL_SOURCES}
        sources = mock.patch.object(models, "sources", return_value=list(models.MODEL_SOURCES))
        sources.start()
        self.addCleanup(sources.stop)

    def refresh(self, **kwargs):
        return models.refresh(registry=kwargs.pop("registry", registry()), opener=opener_for(self.pages), codex_cache=self.cache, **kwargs)

    def test_helpers(self) -> None:
        self.assertEqual(models.version_key("claude-sonnet-5-1"), ("claude-sonnet", (5, 1, 0)))
        self.assertEqual(models.version_key("gpt-6-luna"), ("gpt-luna", (6,)))
        self.assertGreater(models.version_key("gpt-6.1-luna")[1], models.version_key("gpt-6-luna")[1])
        self.assertIsNone(models.version_key("sonnet"))
        self.assertTrue(models.is_outdated("Older balanced model"))
        self.assertTrue(models.is_outdated("Legacy coding model."))
        self.assertFalse(models.is_outdated("Workhorse model"))
        self.assertEqual(models.described_tier("Frontier intelligence for the most demanding work."), "frontier")
        self.assertEqual(models.described_tier("Fast and affordable model"), "fast")
        self.assertEqual(models.described_tier("Workhorse model for coding"), "balanced")

    def test_refresh_merges_sources_and_proposes_like_for_like(self) -> None:
        view = self.refresh()
        catalog = models.load()
        self.assertIn("claude-sonnet-5", catalog["models"])
        self.assertEqual(sorted(catalog["models"]["gpt-6-sol"]["sources"]), ["codex-cli-catalog", "openai-api-models", "openai-codex-models"])
        self.assertTrue(catalog["models"]["gpt-5.6-terra"]["outdated"])
        self.assertEqual([check["ok"] for check in view["checks"]], [True, True, True, True])
        self.assertEqual(view["new_notices"], [], "the first refresh is a baseline, not news")
        proposal = next(item for item in view["proposals"] if item["tier"] == "balanced")
        self.assertEqual(proposal["candidate"], "gpt-6-sol", "never the costlier frontier model for balanced work")
        self.assertIn("Older balanced model", proposal["reason"])

    def test_new_model_and_newer_version_on_later_refresh(self) -> None:
        self.refresh()
        self.pages[models.MODEL_SOURCES[0]["url"]] = CLAUDE_PAGE + " claude-sonnet-5-1 is new."
        codex_cache(self.cache, [{"slug": "gpt-6.1-luna", "visibility": "list", "priority": 3, "description": "Fast and affordable model for easier tasks."}])
        view = self.refresh()
        texts = [notice["text"] for notice in view["new_notices"]]
        self.assertTrue(any("claude-sonnet-5-1" in text for text in texts))
        self.assertTrue(any("gpt-6.1-luna" in text for text in texts))
        self.assertIn("codex:fast:gpt-6.1-luna", [item["id"] for item in view["proposals"]])

    def test_alias_resolution_is_tracked_and_newer_version_proposed(self) -> None:
        ledger = Ledger(lambda run_id: Path(os.environ["AGENT_OS_ORCHESTRATOR_HOME"]) / "runs" / run_id)
        ledger.emit("r1", "model_completed", "n", provider="claude-code", model="sonnet", role="reviewer", usage=normalized(total_input=1, output=1, source="claude-code", model_resolved="claude-sonnet-5"))
        self.refresh()
        self.assertEqual(models.load()["aliases"]["claude-code:sonnet"]["resolved"], "claude-sonnet-5")
        self.pages[models.MODEL_SOURCES[0]["url"]] = CLAUDE_PAGE + " claude-sonnet-5-1"
        view = self.refresh()
        proposal = next(item for item in view["proposals"] if item["provider"] == "claude-code")
        self.assertEqual((proposal["tier"], proposal["candidate"]), ("balanced", "claude-sonnet-5-1"))
        self.assertIn("currently runs claude-sonnet-5", proposal["reason"])
        ledger.emit("r2", "model_completed", "n", provider="claude-code", model="sonnet", role="reviewer", usage=normalized(total_input=1, output=1, source="claude-code", model_resolved="claude-sonnet-5-1"))
        moved = self.refresh()["new_notices"]
        self.assertTrue(any(notice["kind"] == "alias_moved" for notice in moved))

    def test_model_that_stops_being_listed_is_flagged(self) -> None:
        self.refresh()
        path = self.cache
        data = json.loads(path.read_text(encoding="utf-8"))
        data["models"] = [item for item in data["models"] if item["slug"] != "gpt-6-luna"]
        path.write_text(json.dumps(data), encoding="utf-8")
        self.pages = {url: page.replace("gpt-6-luna", "") for url, page in self.pages.items()}
        data["models"].append({"slug": "gpt-6-nova", "visibility": "list", "priority": 3, "description": "Fast and affordable model for easier tasks."})
        path.write_text(json.dumps(data), encoding="utf-8")
        view = self.refresh()
        self.assertTrue(any(notice["kind"] == "model_missing" and notice["model"] == "gpt-6-luna" for notice in view["new_notices"]))
        proposal = next(item for item in view["proposals"] if item["tier"] == "fast" and item["provider"] == "codex")
        self.assertEqual(proposal["candidate"], "gpt-6-nova")
        self.assertIn("no longer listed", proposal["reason"])

    def test_failing_source_does_not_mark_models_missing(self) -> None:
        self.refresh()
        self.pages = {url: OSError("down") for url in self.pages}
        view = self.refresh(online=True)
        self.assertFalse(any(notice["kind"] == "model_missing" and "anthropic" in notice["text"] for notice in view["new_notices"]))
        self.assertNotIn("missing_since", models.load()["models"]["claude-sonnet-5"])

    def test_failing_source_is_recorded_not_fatal(self) -> None:
        self.pages[models.MODEL_SOURCES[1]["url"]] = OSError("offline")
        view = self.refresh()
        failed = [check for check in view["checks"] if not check["ok"]]
        self.assertEqual(len(failed), 1)
        self.assertIn("offline", failed[0]["error"])
        self.assertIn("gpt-6-sol", models.load()["models"])

    def test_offline_refresh_uses_local_catalog_only(self) -> None:
        view = self.refresh(online=False)
        self.assertEqual([check["source"] for check in view["checks"]], ["codex-cli-catalog"])

    def test_apply_writes_override_with_backup_and_registry_honours_it(self) -> None:
        self.refresh()
        path = self.tmp / "providers.json"
        path.write_text(json.dumps({"providers": [{"id": "codex", "adapter": "codex_cli", "discover": False, "models": {"balanced": "gpt-5.6-terra"}}]}), encoding="utf-8")
        applied = models.decide("codex:balanced:gpt-6-sol", True, registry_file=path)
        self.assertEqual(applied["status"], "applied")
        self.assertTrue(Path(applied["backup"]).exists())
        self.assertEqual(ProviderRegistry(path).get("codex")["models"]["balanced"], "gpt-6-sol")
        self.assertEqual(models.view(registry=registry())["proposals"], [], "decided proposals leave the open list")
        self.assertNotIn("codex:balanced:gpt-6-sol", [item["id"] for item in self.refresh()["proposals"]], "and are not re-proposed")

    def test_override_beats_discovery(self) -> None:
        registry_ = ProviderRegistry(providers=[{"id": "codex", "adapter": "codex_cli", "discover": True, "models": {"balanced": "x"}, "model_overrides": {"balanced": "gpt-6-sol"}}], discover=True)
        self.assertEqual(registry_.get("codex")["models"]["balanced"], "gpt-6-sol")

    def test_staleness(self) -> None:
        self.assertTrue(models.is_stale())
        self.refresh()
        self.assertFalse(models.is_stale())
        catalog = models.load()
        catalog["refreshed_at"] = "2020-01-01T00:00:00+00:00"
        models._save(catalog)
        self.assertTrue(models.is_stale())


if __name__ == "__main__":
    unittest.main()
