"""The compiled model service catalog (research/model-services/catalog.json)
follows SCHEMA.md and the endpoint path rules. Reads files only; no network."""

from __future__ import annotations

import json
import importlib.util
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator import endpoints, model_profile  # noqa: E402

try:
    from agent_os.orchestrator import model_services  # noqa: E402
except ImportError:  # the services module may not exist in every base
    model_services = None

RESEARCH = ROOT / "projects" / "personal-agent-os" / "research" / "model-services"
CATALOG = RESEARCH / "catalog.json"
REVIEWED_AT = "2026-10-12"

COMPILER_SPEC = importlib.util.spec_from_file_location("compile_catalog", RESEARCH / "compile_catalog.py")
compiler = importlib.util.module_from_spec(COMPILER_SPEC)
COMPILER_SPEC.loader.exec_module(compiler)

# The 28 services the catalog must cover: display name -> catalog id.
REQUIRED = {
    "Synthetic": "synthetic", "NanoGPT": "nanogpt", "Arli AI": "arli-ai", "Venice": "venice", "Chutes": "chutes",
    "Poe": "poe-api", "Featherless": "featherless", "MiniMax": "minimax-m-plan", "Kimi": "kimi-code",
    "Z.ai": "z-ai-glm-coding-plan", "Alibaba Model Studio": "alibaba-cloud-model-studio", "Together": "together-ai",
    "Fireworks": "fireworks-ai", "Groq": "groq", "Cerebras": "cerebras-inference", "DeepInfra": "deepinfra",
    "Novita": "novita-ai", "Nebius": "nebius-token-factory", "NVIDIA": "nvidia-nim-api", "Mistral": "mistral-la-plateforme",
    "DeepSeek": "deepseek-api", "OpenRouter": "openrouter", "Hugging Face Inference Providers": "hugging-face-inference-providers",
    "RunPod": "runpod", "Vast.ai": "vast-ai", "Modal": "modal", "Replicate": "replicate", "fal": "fal",
}
CATEGORIES = ("subscription_allowance", "hosted_api", "custom_hosting", "gateway")
STATUSES = ("preset_ready", "preset_restricted", "bridge_claude_code", "catalog_only", "deferred")
PROTOCOLS = ("openai_chat", "anthropic_messages", "vendor")
SERVICE_MODALITIES = (*model_profile.MODALITIES, "rerank", "tts", "asr", "video")
FINDING_STATUSES = ("confirmed", "contradicted", "unverified")
MEDIA_TASKS = ("image_generation", "image_editing", "asr", "diarization", "tts", "voice_clone", "embedding", "rerank")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _endpoints(catalog: dict, protocol: str | None = None):
    for service in catalog["services"]:
        for endpoint in service["endpoints"]:
            if protocol is None or endpoint["protocol"] == protocol:
                yield service, endpoint


class CatalogShapeTest(unittest.TestCase):
    def setUp(self):
        self.catalog = _catalog()

    def test_schema_and_review_dates(self):
        self.assertEqual(self.catalog["schema"], "personal-agent/model-service-catalog/v1")
        self.assertEqual(self.catalog["reviewed_at"], REVIEWED_AT)
        self.assertEqual(self.catalog["review_interval_days"], 60)
        self.assertIsInstance(self.catalog["gaps"], list)

    def test_services_have_unique_ids_official_sources_and_dates(self):
        ids = [service["id"] for service in self.catalog["services"]]
        self.assertEqual(len(ids), len(set(ids)))
        for service in self.catalog["services"]:
            self.assertTrue(any(source.get("official") is True for source in service["sources"]), service["id"])
            self.assertRegex(service["reviewed_at"], DATE, service["id"])

    def test_required_services_present(self):
        ids = {service["id"] for service in self.catalog["services"]}
        missing = {name: sid for name, sid in REQUIRED.items() if sid not in ids}
        self.assertEqual(missing, {})
        self.assertEqual(len(self.catalog["services"]), 28)

    def test_base_urls_are_https_without_query_or_trailing_slash(self):
        for service, endpoint in _endpoints(self.catalog):
            url = endpoint["base_url"]
            label = f"{service['id']}/{endpoint['id']}"
            self.assertTrue(url.startswith("https://"), label)
            self.assertEqual(urlsplit(url).query, "", label)
            self.assertNotIn("?", url, label)
            self.assertFalse(url.endswith("/"), label)

    def test_enums(self):
        for service in self.catalog["services"]:
            sid = service["id"]
            self.assertIn(service["category"], CATEGORIES, sid)
            self.assertIn(service["integration_status"], STATUSES, sid)
            self.assertIn(service["deployment"], model_profile.DEPLOYMENTS, sid)
            for modality in service["modalities"]:
                self.assertIn(modality, SERVICE_MODALITIES, sid)
            self.assertIn(service["privacy"]["training_on_prompts"], model_profile.TRAINING_ON_PROMPTS, sid)
            self.assertIn(service["privacy"]["weights_location"], model_profile.WEIGHTS_LOCATIONS, sid)
            for endpoint in service["endpoints"]:
                self.assertIn(endpoint["protocol"], PROTOCOLS, sid)
                self.assertIn(endpoint["path_style"], endpoints.PATH_STYLES, sid)
            for plan in service["plans"]:
                billing = plan["billing"]
                self.assertIn(billing["mode"], model_profile.BILLING_MODES, f"{sid}/{plan['id']}")
                self.assertIn(billing["overage"], model_profile.OVERAGE, f"{sid}/{plan['id']}")
                if billing["allowance"] is not None:
                    self.assertIn(billing["allowance"]["unit"], model_profile.ALLOWANCE_UNITS, f"{sid}/{plan['id']}")
                    self.assertIn(billing["allowance"]["reset_window"], model_profile.RESET_WINDOWS, f"{sid}/{plan['id']}")
                self.assertIn(plan["automation_allowed"], (True, False, None), f"{sid}/{plan['id']}")
            for model in service["models"]:
                self.assertIn(model["refusal_profile"], model_profile.REFUSAL_PROFILES, sid)
            for finding in service["findings"]:
                self.assertIn(finding["status"], FINDING_STATUSES, sid)
        for model in self.catalog["models"]:
            self.assertIn(model["refusal_profile"], model_profile.REFUSAL_PROFILES, model["id"])
        for item in self.catalog["media"]:
            self.assertIn(item["task"], MEDIA_TASKS, item["id"])

    def test_abliterated_records_have_evidence(self):
        records = list(self.catalog["models"]) + [model for service in self.catalog["services"] for model in service["models"]]
        abliterated = [record for record in records if record.get("refusal_profile") == "abliterated"]
        self.assertTrue(abliterated)
        for record in abliterated:
            evidence = record.get("refusal_evidence")
            if evidence is None and record.get("catalog_model"):
                evidence = next(m["refusal_evidence"] for m in self.catalog["models"] if m["id"] == record["catalog_model"])
            self.assertTrue(evidence and str(evidence).strip(), record["id"])

    def test_chat_endpoints_have_secret_refs(self):
        for service, endpoint in _endpoints(self.catalog):
            if endpoint["protocol"] in ("openai_chat", "anthropic_messages"):
                self.assertEqual(endpoint["secret_ref"], f"secrets://{service['id']}/{endpoint['id']}")

    def test_served_by_points_at_catalog_services(self):
        ids = {service["id"] for service in self.catalog["services"]}
        for record in self.catalog["models"] + self.catalog["media"]:
            for served in record["served_by"]:
                self.assertIn(served["service"], ids, record["id"])

    def test_fireworks_native_ids_are_verified_and_router_notes_preserved(self):
        expected = {
            "glm-5.3": "accounts/fireworks/models/glm-5p3",
            "minimax-m3": "accounts/fireworks/models/minimax-m3",
            "kimi-k3": "accounts/fireworks/models/kimi-k3",
            "qwen3-embedding-8b": "accounts/fireworks/models/qwen3-embedding-8b",
            "qwen3-reranker-8b": "accounts/fireworks/models/qwen3-reranker-8b",
        }
        records = {r["id"]: r for r in self.catalog["models"] + self.catalog["media"]}
        native = {m["id"] for s in self.catalog["services"] if s["id"] == "fireworks-ai" for m in s["models"]}
        for record_id, model_id in expected.items():
            with self.subTest(record=record_id):
                served = next(s for s in records[record_id]["served_by"] if s["service"] == "fireworks-ai")
                self.assertEqual(served["model_id"], model_id)
                self.assertIn(model_id, native)
                self.assertEqual(served["native_evidence"]["id"], model_id)
                self.assertTrue((RESEARCH / served["native_evidence"]["batch"]).is_file())
                self.assertTrue(served["notes"])
                if record_id in ("glm-5.3", "minimax-m3", "kimi-k3"):
                    self.assertIn("via HF router", served["notes"])

    def test_router_backing_providers_require_native_id_evidence(self):
        unresolved = []
        for record in self.catalog["models"]:
            for index, served in enumerate(record["served_by"]):
                if served.get("source") != "https://router.huggingface.co/v1/models":
                    continue
                if served["service"] == "hugging-face-inference-providers":
                    self.assertIsNotNone(served["model_id"], record["id"])
                    continue
                self.assertIn("via HF router", served["notes"])
                if served["model_id"] is not None:
                    native = next(s for s in self.catalog["services"] if s["id"] == served["service"])
                    self.assertIn(served["model_id"], [m["id"] for m in native["models"]])
                    self.assertEqual(served["native_evidence"]["id"], served["model_id"])
                else:
                    unresolved.append((record["id"], served["service"]))
                    self.assertIn("model_id", served["unknown"])
                    self.assertIn(f"served_by[{index}].model_id", record["unknown"])
                    self.assertTrue(any(f["status"] == "unverified" and served["service"] in f["claim"]
                                        for f in record["findings"]))
        self.assertIn(("glm-5.3-flash", "fireworks-ai"), unresolved)
        self.assertIn(("qwen3.8-27b", "novita-ai"), unresolved)


class EndpointPathTest(unittest.TestCase):
    def setUp(self):
        self.catalog = _catalog()

    def test_chat_url_has_one_chat_completions_and_no_double_v1(self):
        for service, endpoint in _endpoints(self.catalog, "openai_chat"):
            url = endpoints.url(endpoint["base_url"], "chat", endpoint["path_style"])
            self.assertEqual(url.count("/chat/completions"), 1, url)
            self.assertNotIn("/v1/v1", url, url)
            self.assertNotEqual(endpoint["path_style"], "auto", f"{service['id']}/{endpoint['id']}")

    def test_models_path_is_relative_to_api_root(self):
        for service, endpoint in _endpoints(self.catalog):
            path = endpoint["models_path"]
            if path is None:
                continue
            self.assertTrue(path.startswith("/"), service["id"])
            self.assertFalse(path.startswith("/v1/"), service["id"])
            root = endpoints.api_root(endpoint["base_url"], endpoint["path_style"])
            self.assertNotIn("/v1/v1", root + path)

    def test_documented_chat_urls(self):
        expected = {
            ("deepinfra", "default"): "https://api.deepinfra.com/v1/openai/chat/completions",
            ("groq", "default"): "https://api.groq.com/openai/v1/chat/completions",
            ("z-ai-glm-coding-plan", "default"): "https://api.z.ai/api/paas/v4/chat/completions",
            ("z-ai-glm-coding-plan", "coding"): "https://api.z.ai/api/coding/paas/v4/chat/completions",
            ("novita-ai", "default"): "https://api.novita.ai/openai/v1/chat/completions",
            ("nanogpt", "subscription"): "https://nano-gpt.com/api/subscription/v1/chat/completions",
            ("poe-api", "default"): "https://api.poe.com/v1/chat/completions",
            ("deepseek-api", "default"): "https://api.deepseek.com/chat/completions",
            ("nebius-token-factory", "default"): "https://api.tokenfactory.nebius.com/v1/chat/completions",
        }
        found = {(service["id"], endpoint["id"]): endpoints.url(endpoint["base_url"], "chat", endpoint["path_style"])
                 for service, endpoint in _endpoints(self.catalog, "openai_chat")}
        for key, url in expected.items():
            self.assertEqual(found.get(key), url, key)


class ResearchIndexTest(unittest.TestCase):
    def test_readme_lists_every_service_and_gap(self):
        catalog = _catalog()
        readme = (RESEARCH / "README.md").read_text(encoding="utf-8")
        for service in catalog["services"]:
            self.assertIn(f"| {service['id']} |", readme)
        for gap in catalog["gaps"]:
            self.assertIn(f"batch-{gap['batch']}", readme)


class CompilerRegressionTest(unittest.TestCase):
    def test_compiled_artifacts_match_current_research(self):
        catalog = compiler.compile_catalog()
        self.assertEqual(catalog, _catalog())
        self.assertEqual(compiler.render_readme(catalog), (RESEARCH / "README.md").read_text(encoding="utf-8"))

    def test_unverified_media_fields_are_null_with_provenance(self):
        media = {record["id"]: record for record in _catalog()["media"]}
        for record_id, key, explanation in (
            ("qwen3-tts", "endpoint", "did not open the Together TTS API page"),
            ("voxtral", "pricing", "not found on the pages I opened"),
        ):
            record = media[record_id]
            field = f"served_by[0].{key}"
            self.assertIsNone(record["served_by"][0][key])
            self.assertIn(explanation, record["served_by"][0]["notes"])
            self.assertIn(field, record["unknown"])
            self.assertIn(key, record["served_by"][0]["unknown"])
            self.assertTrue(any(f["status"] == "unverified" and field in f["claim"] for f in record["findings"]))
        # Documented endpoints and prices must survive the same mapping.
        self.assertEqual(media["qwen3-tts"]["served_by"][0]["pricing"], "$4.00 per 1M characters")
        self.assertTrue(media["voxtral"]["served_by"][0]["endpoint"].startswith("POST https://api.mistral.ai/v1/audio/transcriptions"))

    def test_unknown_restrictions_and_other_nulls_are_preserved(self):
        services = {record["id"]: record for record in _catalog()["services"]}
        for letter in "ABCDE":
            batch = json.loads((RESEARCH / "raw" / f"batch-{letter}.json").read_text(encoding="utf-8"))
            for raw in batch["records"]:
                compiled = services[raw["id"]]
                for key in ("disallowed_uses", "notes", "automation_allowed"):
                    self.assertEqual(compiled["restrictions"][key], raw["restrictions"][key], (raw["id"], key))
                self.assertEqual(compiled["restrictions"]["documented_clients"], raw["restrictions"]["allowed_clients"])
                for key in ("access", "quotas", "openai_compatible"):
                    self.assertEqual(compiled[key], raw[key], (raw["id"], key))
                self.assertTrue(set(raw["unknown"]).issubset(compiled["unknown"]))
                if raw["restrictions"]["disallowed_uses"] is None:
                    self.assertIn("restrictions.disallowed_uses", compiled["unknown"])
                    self.assertTrue(any(f["status"] == "unverified" and "restrictions.disallowed_uses" in f["claim"]
                                        for f in compiled["findings"]))

    def test_raw_client_list_null_is_not_coerced_to_empty(self):
        decided = compiler.plan("example", "default", compiler.bill("allowance"), clients="raw")
        raw = {"restrictions": {"automation_allowed": None, "allowed_clients": None}}
        compiled = compiler.build_plan(decided, None, raw, {})
        self.assertIsNone(compiled["allowed_clients"])
        self.assertIsNone(compiled["automation_allowed"])
        for value in (None, [], ["Claude Code"]):
            with self.subTest(value=value):
                self.assertEqual(compiler.map_nullable(value, str), value)

    def test_venice_web_allowance_is_not_an_api_quota(self):
        venice = next(record for record in _catalog()["services"] if record["id"] == "venice")
        index, free = next((i, p) for i, p in enumerate(venice["plans"]) if p["id"] == "free")
        self.assertIsNone(free["billing"]["allowance"])
        self.assertEqual(free["billing"]["overage"], "unknown")
        self.assertIn("10 web text prompts/day", free["notes"])
        self.assertIn(f"plans[{index}].billing.allowance", venice["unknown"])
        self.assertTrue(any(f["status"] == "unverified" and "Venice Free" in f["claim"] for f in venice["findings"]))

    def test_missing_batches_are_omitted_and_main_updates_both_outputs(self):
        exists = Path.exists
        complete = _catalog()
        for letter in "ABCDEFG":
            missing = RESEARCH / "raw" / f"batch-{letter}.json"
            with self.subTest(batch=letter), patch.object(Path, "exists", lambda p: False if p == missing else exists(p)):
                catalog = compiler.compile_catalog()
            self.assertEqual([gap["batch"] for gap in catalog["gaps"]], [letter])
            self.assertNotIn(f"raw/batch-{letter}.json", catalog["compiled_from"])
            batch = json.loads(missing.read_text(encoding="utf-8"))
            key = "services" if letter in "ABCDE" else "models" if letter == "F" else "media"
            removed = {record["id"] for record in batch["records"]}
            self.assertFalse(removed.intersection(record["id"] for record in catalog[key]))
            self.assertEqual(len(catalog[key]), len(complete[key]) - len(removed))
            readme = compiler.render_readme(catalog)
            self.assertIn(f"`batch-{letter}.json`:", readme)
            self.assertNotIn("**Current gaps: none.**", readme)
            if model_services is not None:
                self.assertEqual(model_services.validate(catalog, today=REVIEWED_AT)["errors"], [])

        # Exercise the writer without touching the real staged inputs/outputs.
        out, readme_out = Mock(), Mock()
        with patch.object(compiler, "compile_catalog", return_value=catalog), patch.object(compiler, "OUT", out), patch.object(compiler, "README", readme_out), patch("builtins.print"):
            compiler.main()
        self.assertEqual(json.loads(out.write_text.call_args.args[0]), catalog)
        self.assertEqual(readme_out.write_text.call_args.args[0], compiler.render_readme(catalog))


@unittest.skipIf(model_services is None, "agent_os.orchestrator.model_services is not in this base")
class ModuleValidationTest(unittest.TestCase):
    def test_validate_reports_no_errors(self):
        result = model_services.validate(model_services.load(), today=REVIEWED_AT)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["warnings"], [])

    def test_presets_follow_integration_status(self):
        catalog = model_services.load()
        for service in catalog["services"]:
            sid, status = service["id"], service["integration_status"]
            if status == "preset_ready":
                plan = next(p["id"] for p in service["plans"] if p["automation_allowed"] is True and p["allowed_clients"] is None)
                entry = model_services.preset_entry(sid, model="probe-model", classes=["fast"], plan=plan, catalog=catalog, today=REVIEWED_AT)
                self.assertTrue(entry["options"]["secret_ref"].startswith(f"secrets://{sid}/"), sid)
            elif status == "preset_restricted":
                plan = next(p["id"] for p in service["plans"] if p["automation_allowed"] is None and p["allowed_clients"] is None)
                with self.assertRaises(ValueError, msg=sid):
                    model_services.preset_entry(sid, model="probe-model", classes=["fast"], plan=plan, catalog=catalog, today=REVIEWED_AT)
                entry = model_services.preset_entry(sid, model="probe-model", classes=["fast"], plan=plan, ack_terms=True,
                                                    catalog=catalog, today=REVIEWED_AT)
                self.assertEqual(entry["options"]["terms_ack"]["service"], sid)
            elif status == "bridge_claude_code":
                entry = model_services.bridge_entry(sid, ack_terms=True, catalog=catalog, today=REVIEWED_AT)
                self.assertTrue(entry["options"]["env"]["ANTHROPIC_BASE_URL"].startswith("https://"), sid)
                self.assertTrue(entry["options"]["secret_env"]["ANTHROPIC_AUTH_TOKEN"].startswith(f"secrets://{sid}/"), sid)
            else:
                with self.assertRaises(ValueError, msg=sid):
                    model_services.preset_entry(sid, model="probe-model", classes=["fast"], ack_terms=True, catalog=catalog, today=REVIEWED_AT)


if __name__ == "__main__":
    unittest.main()
