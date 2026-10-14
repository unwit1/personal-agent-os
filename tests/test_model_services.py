"""Model service catalog: validation, presets, the Claude Code bridge and
read-only discovery. Synthetic catalogs and fake transports only; no network."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import main  # noqa: E402
from agent_os.orchestrator import model_services  # noqa: E402
from agent_os.orchestrator.adapters.base import AgentLaunchRequest  # noqa: E402
from agent_os.orchestrator.adapters.http_api import OpenAiCompatibleAdapter  # noqa: E402
from agent_os.orchestrator.model_profile import is_paid  # noqa: E402

PLACEHOLDER_KEY = "placeholder-key-value-for-tests-only"
TODAY = "2026-10-12"


def _source(official: bool = True) -> dict:
    return {"url": "https://example.com/docs", "title": "Docs", "accessed": TODAY, "official": official}


def _service(service_id: str, **overrides) -> dict:
    record = {
        "id": service_id, "name": service_id.title(), "category": "subscription_allowance", "homepage": "https://example.com",
        "reviewed_at": TODAY, "integration_status": "preset_ready", "integration_notes": "synthetic",
        "deployment": "subscription", "modalities": ["text", "code"],
        "endpoints": [{"id": "default", "protocol": "openai_chat", "base_url": f"https://api.{service_id}.example/v1", "path_style": "root",
                       "models_path": "/models", "models_list_requires_auth": True, "secret_ref": f"secrets://{service_id}/default", "notes": ""}],
        "plans": [{"id": "pro", "name": "Pro", "usd_per_month": 10, "endpoint": "default",
                   "billing": {"mode": "allowance", "plan": "pro", "allowance": {"unit": "requests", "amount": 1000, "reset_window": "daily"},
                               "overage": "blocked", "metered_triggers": []},
                   "automation_allowed": True, "allowed_clients": None, "notes": ""}],
        "privacy": {"training_on_prompts": "no", "retention": None, "zdr": None, "weights_location": "third_party"},
        "restrictions": {"disallowed_uses": [], "notes": ""}, "quotas": {"rate_limits": None, "concurrency": None, "context_caps": None},
        "models": [{"id": "open-coder", "catalog_model": "open-coder", "open_weights": True, "license": "apache-2.0",
                    "refusal_profile": "standard", "context_window": 131072, "modalities": ["text", "code"]}],
        "findings": [], "unknown": ["privacy.retention"], "sources": [_source()],
    }
    record.update(overrides)
    return record


def synthetic_catalog() -> dict:
    legacy = _service("legacy", category="hosted_api", deployment="api")
    legacy["endpoints"][0].update({"base_url": "https://legacy.example/openai", "path_style": "append_v1"})
    legacy["plans"][0]["billing"] = {"mode": "allowance", "plan": "pro", "allowance": {"unit": "requests", "amount": None, "reset_window": "monthly"},
                                     "overage": "unknown", "metered_triggers": []}
    forbidden = _service("forbidden", integration_status="catalog_only")
    forbidden["plans"][0]["automation_allowed"] = False
    unclear = _service("unclear", integration_status="preset_restricted")
    unclear["plans"][0]["automation_allowed"] = None
    coding = _service("coding", integration_status="bridge_claude_code")
    coding["endpoints"].append({"id": "anthropic", "protocol": "anthropic_messages", "base_url": "https://api.coding.example/api/anthropic",
                                "path_style": "auto", "models_path": None, "models_list_requires_auth": None,
                                "secret_ref": "secrets://coding/anthropic", "notes": ""})
    coding["plans"] = [{"id": "coding-plan", "name": "Coding plan", "usd_per_month": 3, "endpoint": "default",
                        "billing": {"mode": "allowance", "plan": "coding", "allowance": {"unit": "prompts", "amount": 120, "reset_window": "5h_rolling"},
                                    "overage": "blocked", "metered_triggers": []},
                        "automation_allowed": True, "allowed_clients": ["Claude Code", "Kimi CLI"], "notes": ""},
                       {"id": "bridge-plan", "name": "Coding plan (Claude Code)", "usd_per_month": 3, "endpoint": "anthropic",
                        "billing": {"mode": "allowance", "plan": "coding", "allowance": {"unit": "prompts", "amount": 120, "reset_window": "5h_rolling"},
                                    "overage": "blocked", "metered_triggers": []},
                        "automation_allowed": True, "allowed_clients": ["Claude Code"], "notes": ""}]
    public = _service("public")
    public["endpoints"][0].update({"models_list_requires_auth": False})
    nolist = _service("nolist")
    nolist["endpoints"][0]["models_path"] = None
    return {
        "schema": model_services.SCHEMA, "reviewed_at": TODAY, "review_interval_days": 60,
        "services": [_service("alpha"), legacy, forbidden, unclear, coding, public, nolist],
        "models": [{"id": "open-coder", "name": "Open Coder", "hf_repos": ["org/open-coder"], "family": "coder", "base_model": None,
                    "params_total_b": 30, "params_active_b": 3, "license": "apache-2.0", "open_weights": True, "context_window": 262144,
                    "released": "2026-01-01", "refusal_profile": "standard", "refusal_evidence": None, "abliteration_method": None,
                    "vs_base": None, "served_by": [{"service": "alpha", "model_id": "open-coder"}], "benchmarks_prior": [],
                    "suggested_prior_task_families": ["coding"], "unknown": [], "sources": [_source(False)], "notes": ""}],
        "media": [],
    }


class FakeResponse:
    def __init__(self, payload) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


class FakeOpener:
    def __init__(self, payload=None, error: Exception | None = None) -> None:
        self.requests = []
        self.payload = payload if payload is not None else {"data": [{"id": "open-coder", "owned_by": "org", "context_length": 131072}, {"id": "other"}]}
        self.error = error

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        if self.error:
            raise self.error
        return FakeResponse(self.payload)


class ValidateTests(unittest.TestCase):
    def test_synthetic_catalog_is_valid(self) -> None:
        result = model_services.validate(synthetic_catalog(), today=TODAY)
        self.assertEqual(result["errors"], [])

    def test_errors(self) -> None:
        catalog = synthetic_catalog()
        catalog["services"][0]["sources"] = [_source(False)]
        catalog["services"][1]["category"] = "bogus"
        catalog["services"].append(copy.deepcopy(catalog["services"][2]))
        catalog["models"].append({**copy.deepcopy(catalog["models"][0]), "id": "open-coder-abliterated", "refusal_profile": "abliterated"})
        errors = model_services.validate(catalog, today=TODAY)["errors"]
        self.assertTrue(any("alpha" in item and "official source" in item for item in errors), errors)
        self.assertTrue(any("legacy" in item and "category 'bogus'" in item for item in errors), errors)
        self.assertTrue(any("forbidden" in item and "duplicate service id" in item for item in errors), errors)
        self.assertTrue(any("open-coder-abliterated" in item and "refusal_evidence" in item for item in errors), errors)

    def test_stale_is_a_warning(self) -> None:
        catalog = synthetic_catalog()
        catalog["services"][0]["reviewed_at"] = "2026-01-01"
        result = model_services.validate(catalog, today=TODAY)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("alpha" in item and "stale" in item for item in result["warnings"]), result["warnings"])
        rows = {row["id"]: row for row in model_services.services(catalog, today=TODAY)}
        self.assertTrue(rows["alpha"]["stale"])
        self.assertFalse(rows["legacy"]["stale"])

    def test_real_catalog_validates_when_compiled(self) -> None:
        if not model_services.CATALOG_PATH.exists():
            self.skipTest("catalog.json not compiled yet")
        self.assertEqual(model_services.validate(model_services.load())["errors"], [])

    def test_missing_catalog_is_reported(self) -> None:
        missing = Path(tempfile.gettempdir()) / "agent-os-no-such-catalog.json"
        with self.assertRaises(FileNotFoundError) as ctx:
            model_services.load(missing)
        self.assertIn("catalog not compiled yet", str(ctx.exception))
        with mock.patch.object(model_services, "CATALOG_PATH", missing):
            result = model_services.services()
        self.assertEqual(result["error"], "catalog not compiled yet")


class PresetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = synthetic_catalog()

    def chat_url(self, entry: dict) -> str:
        request = AgentLaunchRequest(run_id="r", node_id="n", role="inline", cwd=".", prompt_path="p", output_dir="o",
                                     capability_class="fast", effort="low", model=entry["models"]["fast"], provider_effort=None, read_only=True)
        with mock.patch("agent_os.orchestrator.secret_refs.resolve", return_value=None):
            return OpenAiCompatibleAdapter(entry).request_body(request, "hi")[0]

    def test_root_style_endpoint_has_one_v1(self) -> None:
        entry = model_services.preset_entry("alpha", model="open-coder", classes=["fast"], catalog=self.catalog, today=TODAY)
        url = self.chat_url(entry)
        self.assertEqual(url, "https://api.alpha.example/v1/chat/completions")
        self.assertEqual(url.count("/v1"), 1)
        self.assertEqual(entry["id"], "alpha")
        self.assertEqual(entry["adapter"], "openai_api")
        self.assertEqual(entry["costs"], {"fast": 1.0})
        self.assertEqual(entry["max_concurrency"], 2)
        self.assertEqual(entry["roles"], ["inline"])
        self.assertEqual(entry["options"]["secret_ref"], "secrets://alpha/default")
        self.assertEqual(entry["profile"]["license"], "apache-2.0")
        self.assertEqual(entry["profile"]["context_window"], 131072)
        self.assertNotIn("terms_ack", entry["options"])
        # No provider-selection or routing request parameters.
        self.assertLessEqual(set(entry["options"]), {"base_url", "send_reasoning_effort", "secret_ref", "path_style", "catalog"})

    def test_legacy_style_endpoint(self) -> None:
        entry = model_services.preset_entry("legacy", model="open-coder", classes=["fast", "balanced"], catalog=self.catalog)
        self.assertEqual(self.chat_url(entry), "https://legacy.example/openai/v1/chat/completions")
        self.assertEqual(entry["options"]["path_style"], "append_v1")

    def test_provider_id_for_non_default_endpoint(self) -> None:
        self.catalog["services"][0]["endpoints"][0]["id"] = "subscription"
        self.catalog["services"][0]["plans"][0]["endpoint"] = "subscription"
        entry = model_services.preset_entry("alpha", model="m", classes=["fast"], catalog=self.catalog)
        self.assertEqual(entry["id"], "alpha-subscription")
        self.assertEqual(entry["profile"]["refusal_profile"], "unknown")

    def test_automation_false_refuses(self) -> None:
        with self.assertRaisesRegex(ValueError, "do not allow automated use"):
            model_services.preset_entry("forbidden", model="m", classes=["fast"], catalog=self.catalog, ack_terms=True)

    def test_unclear_terms_need_ack(self) -> None:
        with self.assertRaisesRegex(ValueError, "ack-terms"):
            model_services.preset_entry("unclear", model="m", classes=["fast"], catalog=self.catalog)
        entry = model_services.preset_entry("unclear", model="m", classes=["fast"], catalog=self.catalog, ack_terms=True, today=TODAY)
        self.assertEqual(entry["options"]["terms_ack"], {"service": "unclear", "plan": "pro", "at": TODAY})

    def test_allowed_clients_refusal_points_to_bridge(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            model_services.preset_entry("coding", model="m", classes=["fast"], plan="coding-plan", catalog=self.catalog)
        self.assertIn("Claude Code", str(ctx.exception))
        self.assertIn("bridge", str(ctx.exception))
        # The suggested `services bridge coding --plan coding-plan` must work.
        entry = model_services.bridge_entry("coding", plan="coding-plan", models={"sonnet": "glm-5.1"}, catalog=self.catalog)
        self.assertEqual(entry["options"]["env"]["ANTHROPIC_BASE_URL"], "https://api.coding.example/api/anthropic")
        self.assertEqual(entry["options"]["catalog"], {"service": "coding", "endpoint": "anthropic", "plan": "coding-plan"})
        self.assertEqual(entry["profile"]["billing"]["plan"], "coding")

    def test_null_secret_ref_defaults_and_never_uses_openai_key(self) -> None:
        self.catalog["services"][0]["endpoints"][0]["secret_ref"] = None
        entry = model_services.preset_entry("alpha", model="m", classes=["fast"], catalog=self.catalog)
        self.assertEqual(entry["options"]["secret_ref"], "secrets://alpha/default")
        request = AgentLaunchRequest(run_id="r", node_id="n", role="inline", cwd=".", prompt_path="p", output_dir="o",
                                     capability_class="fast", effort="low", model="m", provider_effort=None, read_only=True)
        with mock.patch.dict("os.environ", {"OPENAI_API_KEY": PLACEHOLDER_KEY}), \
                mock.patch("agent_os.orchestrator.secret_refs.resolve", return_value=None):
            headers = OpenAiCompatibleAdapter(entry).request_body(request, "hi")[2]
        self.assertEqual(headers, {})
        self.catalog["services"][4]["endpoints"][1]["secret_ref"] = None
        bridge = model_services.bridge_entry("coding", catalog=self.catalog)
        self.assertEqual(bridge["options"]["secret_env"], {"ANTHROPIC_AUTH_TOKEN": "secrets://coding/anthropic"})

    def test_bridge_picks_claude_code_plan_and_anthropic_endpoint(self) -> None:
        coding = self.catalog["services"][4]
        # A plan without client restriction first: plan=None still picks the
        # first plan that lists Claude Code.
        coding["plans"].insert(0, {**copy.deepcopy(coding["plans"][0]), "id": "payg", "allowed_clients": None,
                                   "billing": {"mode": "metered", "plan": "payg", "allowance": None, "overage": "metered", "metered_triggers": []}})
        entry = model_services.bridge_entry("coding", catalog=self.catalog)
        self.assertEqual(entry["options"]["catalog"], {"service": "coding", "endpoint": "anthropic", "plan": "coding-plan"})
        self.assertEqual(entry["options"]["env"]["ANTHROPIC_BASE_URL"], "https://api.coding.example/api/anthropic")
        self.assertEqual(entry["profile"]["billing"]["plan"], "coding")

    def test_bridge_entry_shape(self) -> None:
        entry = model_services.bridge_entry("coding", models={"sonnet": "glm-5.1", "opus": "glm-5.1"}, catalog=self.catalog)
        self.assertEqual(entry["adapter"], "claude_code")
        self.assertEqual(entry["options"]["env"], {"ANTHROPIC_BASE_URL": "https://api.coding.example/api/anthropic",
                                                   "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5.1", "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5.1"})
        self.assertEqual(entry["options"]["secret_env"], {"ANTHROPIC_AUTH_TOKEN": "secrets://coding/anthropic"})
        self.assertEqual(entry["models"], {"balanced": "sonnet", "reasoning": "opus"})
        self.assertEqual(entry["costs"], {"balanced": 1.0, "reasoning": 1.0})
        self.assertEqual(entry["roles"], ["inline", "planner"])
        self.assertEqual(entry["profile"]["billing"]["plan"], "coding")
        self.assertFalse(is_paid(entry))
        with self.assertRaisesRegex(ValueError, "model map keys"):
            model_services.bridge_entry("coding", models={"gpt": "x"}, catalog=self.catalog)

    def test_billing_propagation_and_paid_semantics(self) -> None:
        blocked = model_services.preset_entry("alpha", model="m", classes=["fast"], catalog=self.catalog)
        self.assertEqual(blocked["profile"]["billing"]["overage"], "blocked")
        self.assertEqual(blocked["profile"]["billing"]["allowance"], {"unit": "requests", "amount": 1000, "reset_window": "daily"})
        self.assertEqual(blocked["profile"]["privacy"]["training_on_prompts"], "no")
        self.assertFalse(is_paid(blocked))
        unknown = model_services.preset_entry("legacy", model="m", classes=["fast"], catalog=self.catalog)
        self.assertEqual(unknown["profile"]["billing"]["overage"], "unknown")
        self.assertTrue(is_paid(unknown))
        row = next(item for item in model_services.services(self.catalog) if item["id"] == "alpha")
        self.assertEqual(row["plans"][0]["allowance_summary"], "allowance 1000 requests / daily, overage blocked")
        self.assertEqual(row["endpoints"], [{"id": "default", "protocol": "openai_chat", "base_url": "https://api.alpha.example/v1"}])


class DiscoverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = synthetic_catalog()
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)

    def test_get_with_key_and_cache(self) -> None:
        opener = FakeOpener()
        models = model_services.discover("alpha", opener=opener, resolve=lambda ref: PLACEHOLDER_KEY, home=self.home.name, catalog=self.catalog)
        self.assertEqual([item["id"] for item in models], ["open-coder", "other"])
        self.assertEqual(models[0], {"id": "open-coder", "owned_by": "org", "context_length": 131072})
        request = opener.requests[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIsNone(request.data)
        self.assertEqual(request.full_url, "https://api.alpha.example/v1/models")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {PLACEHOLDER_KEY}")
        cache = Path(self.home.name) / "service-models" / "alpha--default.json"
        text = cache.read_text(encoding="utf-8")
        self.assertNotIn(PLACEHOLDER_KEY, text)
        self.assertNotIn(PLACEHOLDER_KEY, json.dumps(models))
        cached = model_services.cached_models("alpha", home=self.home.name, catalog=self.catalog)
        self.assertEqual(set(cached), {"fetched_at", "service", "endpoint", "models"})
        self.assertEqual(cached["models"], models)

    def test_no_authorization_without_key(self) -> None:
        opener = FakeOpener()
        model_services.discover("public", opener=opener, resolve=lambda ref: None, home=self.home.name, catalog=self.catalog)
        self.assertIsNone(opener.requests[0].get_header("Authorization"))

    def test_missing_models_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "models_path is null"):
            model_services.discover("nolist", opener=FakeOpener(), resolve=lambda ref: None, home=self.home.name, catalog=self.catalog)

    def test_missing_required_key_names_secret_ref(self) -> None:
        opener = FakeOpener()
        with self.assertRaisesRegex(ValueError, "secrets://alpha/default"):
            model_services.discover("alpha", opener=opener, resolve=lambda ref: None, home=self.home.name, catalog=self.catalog)
        self.assertEqual(opener.requests, [])

    def test_http_error_hides_key(self) -> None:
        error = urllib.error.HTTPError("https://api.alpha.example/v1/models", 401, f"bad key {PLACEHOLDER_KEY}", {}, None)
        with self.assertRaises(ValueError) as ctx:
            model_services.discover("alpha", opener=FakeOpener(error=error), resolve=lambda ref: PLACEHOLDER_KEY, home=self.home.name, catalog=self.catalog)
        self.assertIn("HTTP 401", str(ctx.exception))
        self.assertNotIn(PLACEHOLDER_KEY, str(ctx.exception))
        self.assertFalse((Path(self.home.name) / "service-models" / "alpha--default.json").exists())


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog_path = Path(self.tmp.name) / "catalog.json"
        self.catalog_path.write_text(json.dumps(synthetic_catalog()), encoding="utf-8")
        self.registry = Path(self.tmp.name) / "providers.json"

    def run_cli(self, *argv: str) -> tuple[int, object]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch("agent_os.orchestrator.secret_refs.resolve", return_value=None):
            code = main(["orchestrate", "services", *argv])
        return code, json.loads(out.getvalue())

    def test_list_and_add_preview(self) -> None:
        code, rows = self.run_cli("list", "--catalog", str(self.catalog_path), "--status", "preset_ready")
        self.assertEqual(code, 0)
        self.assertEqual({row["id"] for row in rows}, {"alpha", "legacy", "public", "nolist"})
        code, result = self.run_cli("add", "alpha", "--catalog", str(self.catalog_path), "--model", "open-coder", "--path", str(self.registry))
        self.assertEqual(code, 0)
        self.assertFalse(result["written"])
        self.assertEqual(result["path"], str(self.registry))
        self.assertEqual(result["entry"]["models"], {"fast": "open-coder", "balanced": "open-coder"})
        self.assertFalse(self.registry.exists())
        code, result = self.run_cli("bridge", "coding", "--catalog", str(self.catalog_path), "--model-map", "sonnet=glm-5.1", "--path", str(self.registry))
        self.assertEqual(code, 0)
        self.assertEqual(result["entry"]["options"]["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"], "glm-5.1")
        self.assertFalse(self.registry.exists())

    def test_validate_and_refusal_exit_codes(self) -> None:
        code, result = self.run_cli("validate", "--catalog", str(self.catalog_path))
        self.assertEqual((code, result["errors"]), (0, []))
        code, result = self.run_cli("add", "forbidden", "--catalog", str(self.catalog_path), "--model", "m", "--path", str(self.registry))
        self.assertNotEqual(code, 0)
        self.assertIn("automated use", result["error"])

    def test_missing_catalog(self) -> None:
        code, result = self.run_cli("list", "--catalog", str(Path(self.tmp.name) / "missing.json"))
        self.assertEqual(code, 1)
        self.assertEqual(result["error"], "catalog not compiled yet")


if __name__ == "__main__":
    unittest.main()
