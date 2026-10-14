"""Control GUI: the model services routes, the registered-foreman routes and
the panel markup. Synthetic catalog, temp registry and home; no network."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_model_services import PLACEHOLDER_KEY, FakeOpener, synthetic_catalog  # noqa: E402

from agent_os.capabilities import PROVIDER_REGISTRY_ENV  # noqa: E402
from agent_os.orchestrator import model_services, server  # noqa: E402
from agent_os.orchestrator.store import HOME_ENV  # noqa: E402

GUI = Path(__file__).resolve().parents[1] / "gui"


def _no_network(*args, **kwargs):
    raise AssertionError("the GUI contacted a vendor without being asked")


class ServicesRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.registry = self.root / "providers.json"
        catalog = synthetic_catalog()
        for service in catalog["services"]:  # fresh relative to the real clock, so staleness never drifts
            service["reviewed_at"] = date.today().isoformat()
        catalog["services"][1]["reviewed_at"] = "2025-01-01"  # legacy: stale
        self.catalog_path = self.root / "catalog.json"
        self.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        self.opener = FakeOpener()
        self.engine = mock.Mock()
        self.key = None
        for patcher in (mock.patch.object(model_services, "CATALOG_PATH", self.catalog_path),
                        mock.patch.object(model_services, "_default_opener", self.opener),
                        mock.patch("agent_os.orchestrator.secret_refs.resolve", side_effect=lambda ref: self.key),
                        mock.patch("agent_os.orchestrator.service.engine", return_value=self.engine),
                        mock.patch.dict(os.environ, {PROVIDER_REGISTRY_ENV: str(self.registry), HOME_ENV: str(self.root / "home")})):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.api = server.Api(server.Drivers())

    def test_list_shows_rows_with_plans_privacy_stale_and_the_warning_count(self) -> None:
        view = self.api.get("/api/services", {})
        rows = {row["id"]: row for row in view["services"]}
        self.assertEqual(set(rows), {"alpha", "legacy", "forbidden", "unclear", "coding", "public", "nolist"})
        self.assertTrue(rows["legacy"]["stale"])
        self.assertFalse(rows["alpha"]["stale"])
        self.assertIn("allowance 1000 requests", rows["alpha"]["plans"][0]["allowance_summary"])
        self.assertEqual(rows["alpha"]["privacy"]["training_on_prompts"], "no")
        self.assertTrue(rows["unclear"]["plans"][0]["needs_ack"])
        expected = model_services.validate(model_services.load())
        self.assertEqual((view["warnings"], view["errors"]), (len(expected["warnings"]), 0))
        self.assertGreaterEqual(view["warnings"], 1)
        self.assertEqual(self.opener.requests, [])  # opening the panel reads the local catalog only

    def test_missing_catalog_is_a_notice_not_an_error(self) -> None:
        with mock.patch.object(model_services, "CATALOG_PATH", self.root / "absent.json"):
            view = self.api.get("/api/services", {})
        self.assertEqual(view["notice"], model_services.NOT_COMPILED)
        self.assertNotIn("error", view)  # the GUI's api() treats "error" as a failure
        self.assertEqual(view["services"], [])

    def test_show_one_service_and_unknown_is_refused(self) -> None:
        detail = self.api.get("/api/services/alpha", {})
        self.assertEqual((detail["id"], detail["models"][0]["id"]), ("alpha", "open-coder"))
        with self.assertRaisesRegex(ValueError, "unknown model service"):
            self.api.get("/api/services/nope", {})
        self.assertEqual(self.opener.requests, [])

    def test_discover_returns_model_ids_with_a_get_and_never_the_key(self) -> None:
        self.key = PLACEHOLDER_KEY
        result = self.api.post("/api/services/discover", {"service": "alpha", "endpoint": "default"})
        self.assertEqual(result["models"], ["open-coder", "other"])
        self.assertEqual([request.get_method() for request in self.opener.requests], ["GET"])
        self.assertNotIn(PLACEHOLDER_KEY, json.dumps(result))
        cached = model_services.cached_models("alpha", "default", home=self.root / "home")
        self.assertEqual([item["id"] for item in cached["models"]], ["open-coder", "other"])

    def test_discover_without_a_needed_key_names_the_secret_ref(self) -> None:
        with self.assertRaisesRegex(ValueError, "secrets://alpha/default"):
            self.api.post("/api/services/discover", {"service": "alpha"})

    def test_add_previews_then_writes_and_resets_the_providers_cache(self) -> None:
        self.key = PLACEHOLDER_KEY
        body = {"service": "alpha", "model": "open-coder", "classes": "fast,balanced", "roles": ["inline"], "cost": "0.5"}
        self.api._providers_cache = (0.0, [])
        preview = self.api.post("/api/services/add", body)
        self.assertFalse(preview["written"])
        self.assertFalse(self.registry.exists())
        self.assertIsNotNone(self.api._providers_cache)
        entry = preview["entry"]
        self.assertEqual((entry["id"], entry["adapter"], sorted(entry["models"])), ("alpha", "openai_api", ["balanced", "fast"]))
        self.assertEqual(entry["costs"], {"fast": 0.5, "balanced": 0.5})
        self.assertIn("secrets://alpha/default", json.dumps(entry))
        self.assertNotIn(PLACEHOLDER_KEY, json.dumps(preview))
        written = self.api.post("/api/services/add", {**body, "write": True})
        self.assertTrue(written["written"])
        self.assertIsNone(self.api._providers_cache)
        stored = json.loads(self.registry.read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in stored["providers"]], ["alpha"])
        self.assertNotIn(PLACEHOLDER_KEY, self.registry.read_text(encoding="utf-8"))
        self.engine.reload_providers.assert_called()

    def test_add_applies_the_preset_rules(self) -> None:
        with self.assertRaisesRegex(ValueError, "do not allow automated use"):
            self.api.post("/api/services/add", {"service": "forbidden", "model": "open-coder", "classes": ["fast"]})
        with self.assertRaisesRegex(ValueError, "ack_terms"):
            self.api.post("/api/services/add", {"service": "unclear", "model": "open-coder", "classes": ["fast"]})
        acked = self.api.post("/api/services/add", {"service": "unclear", "model": "open-coder", "classes": ["fast"], "ack_terms": True})
        self.assertEqual(acked["entry"]["options"]["terms_ack"]["plan"], "pro")
        with self.assertRaisesRegex(ValueError, "bridge"):
            self.api.post("/api/services/add", {"service": "coding", "model": "open-coder", "classes": ["fast"]})
        with self.assertRaisesRegex(ValueError, "pick a model"):
            self.api.post("/api/services/add", {"service": "alpha", "classes": ["fast"]})
        self.assertFalse(self.registry.exists())

    def test_bridge_builds_a_claude_code_entry(self) -> None:
        result = self.api.post("/api/services/bridge", {"service": "coding", "models": {"sonnet": "glm-5.1"}})
        entry = result["entry"]
        self.assertFalse(result["written"])
        self.assertEqual(entry["adapter"], "claude_code")
        self.assertEqual(entry["options"]["env"]["ANTHROPIC_BASE_URL"], "https://api.coding.example/api/anthropic")
        self.assertEqual(entry["options"]["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"], "glm-5.1")
        self.assertEqual(entry["options"]["secret_env"], {"ANTHROPIC_AUTH_TOKEN": "secrets://coding/anthropic"})
        self.assertFalse(self.registry.exists())


class ForemanRouteTests(unittest.TestCase):
    def test_eligible_and_use_registered_pass_through(self) -> None:
        api = server.Api(server.Drivers())
        manager = mock.Mock()
        manager.use.return_value = {"kind": "registered"}
        with mock.patch("agent_os.orchestrator.foreman_deploy.eligible_foremen", return_value=[{"provider": "plan-api"}]), \
                mock.patch("agent_os.orchestrator.foreman_deploy.manager", return_value=manager):
            self.assertEqual(api.get("/api/foreman/eligible", {}), {"foremen": [{"provider": "plan-api"}]})
            api.post("/api/foreman/use", {"kind": "registered", "provider": "plan-api", "model": "m-large"})
            api.post("/api/foreman/use", {"kind": "claude"})
        first, second = manager.use.call_args_list
        self.assertEqual(first.args, ("registered",))
        self.assertEqual((first.kwargs["provider"], first.kwargs["model"]), ("plan-api", "m-large"))
        self.assertIsNone(second.kwargs["provider"])


class PanelMarkupTests(unittest.TestCase):
    def test_services_panel_and_registered_foreman_are_wired(self) -> None:
        html = (GUI / "index.html").read_text(encoding="utf-8")
        script = (GUI / "simple.js").read_text(encoding="utf-8")
        for element in ("services-panel", "services-list", "services-badge", "fm-reg", "fm-reg-provider", "fm-reg-model", "fm-reg-note", "fm-use-reg"):
            self.assertIn(f'id="{element}"', html)
            self.assertIn(f'"{element}"', script)
        self.assertLess(html.index('id="compute-panel"'), html.index('id="services-panel"'))
        fm_source = html[html.index('id="fm-source"'):html.index("</select>", html.index('id="fm-source"'))]
        quick = html[html.index('id="quick-foreman"'):html.index("</select>", html.index('id="quick-foreman"'))]
        self.assertIn('value="registered"', fm_source)
        self.assertIn('value="registered"', quick)
        for route in ('api("services")', '"services/discover"', '"services/add"', '"services/bridge"', '"foreman/eligible"', "services/${"):
            self.assertIn(route, script)
        for text in ('registered: "Registered provider"', 'kind: "registered"', "Add to my providers", "Add as Claude Code bridge",
                     "I have read this plan's terms", "List models", "Preview", "needs_ack", "stale"):
            self.assertIn(text, script)


if __name__ == "__main__":
    unittest.main()
