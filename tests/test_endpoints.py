"""OpenAI-compatible endpoint path resolution and its HTTP callers."""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import endpoints, foreman_deploy  # noqa: E402
from agent_os.orchestrator.adapters.http_api import OpenAiCompatibleAdapter  # noqa: E402
from agent_os.orchestrator.model_profile import endpoint_entry  # noqa: E402


class EndpointTests(unittest.TestCase):
    def test_legacy_and_hosted_api_roots(self) -> None:
        cases = {
            "http://127.0.0.1:8000": "http://127.0.0.1:8000/v1",
            "https://openrouter.ai/api/": "https://openrouter.ai/api/v1",
            "https://api.together.xyz/v1": "https://api.together.xyz/v1",
            "https://api.groq.com/openai/v1": "https://api.groq.com/openai/v1",
            "https://api.z.ai/api/paas/v4": "https://api.z.ai/api/paas/v4",
            "https://api.deepinfra.com/v1/openai": "https://api.deepinfra.com/v1/openai/v1",
            "https://api.novita.ai/openai": "https://api.novita.ai/openai/v1",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            "https://nano-gpt.com/api/subscription/v1": "https://nano-gpt.com/api/subscription/v1",
            "https://router.huggingface.co/v1/": "https://router.huggingface.co/v1",
            "https://example.com/api/v1beta": "https://example.com/api/v1beta",
            "https://example.com/api/v2alpha3": "https://example.com/api/v2alpha3",
        }
        for base, expected in cases.items():
            with self.subTest(base=base):
                self.assertEqual(endpoints.api_root(base), expected)

    def test_styles_and_resource_paths(self) -> None:
        self.assertEqual(endpoints.PATH_STYLES, ("auto", "append_v1", "root"))
        self.assertEqual(endpoints.api_root("https://example.com/v4/", "append_v1"), "https://example.com/v4/v1")
        self.assertEqual(endpoints.api_root("https://example.com/api/", "root"), "https://example.com/api")
        paths = {
            "chat": "/chat/completions", "models": "/models", "embeddings": "/embeddings",
            "rerank": "/rerank", "images": "/images/generations",
            "transcriptions": "/audio/transcriptions", "speech": "/audio/speech",
        }
        for kind, path in paths.items():
            with self.subTest(kind=kind):
                self.assertEqual(endpoints.url("https://example.com/v1", kind), "https://example.com/v1" + path)
        with self.assertRaisesRegex(ValueError, "path_style"):
            endpoints.api_root("https://example.com", "invalid")
        with self.assertRaisesRegex(ValueError, "kind"):
            endpoints.url("https://example.com", "invalid")

    def test_overrides(self) -> None:
        base = "https://example.com/v4"
        self.assertEqual(endpoints.url(base, "chat", overrides={"chat": "https://elsewhere.test/chat?x=1"}), "https://elsewhere.test/chat?x=1")
        self.assertEqual(endpoints.url(base, "chat", overrides={"chat": "/custom/chat"}), base + "/custom/chat")
        with self.assertRaisesRegex(ValueError, "override"):
            endpoints.url(base, "chat", overrides={"chat": "custom/chat"})

    def test_base_url_validation(self) -> None:
        for bad in ("ftp://example.com", "https:///path", "https://example.com?x=1", "https://example.com#part", "https://user:pass@example.com"):
            with self.subTest(base=bad), self.assertRaises(ValueError):
                endpoints.validate_base_url(bad)
        endpoints.validate_base_url("http://127.0.0.1:8000/v1")

    def test_adapter_uses_style_and_paths(self) -> None:
        request = mock.Mock(model="m", provider_effort=None)
        cases = [
            ({"base_url": "https://api.groq.com/openai/v1"}, "https://api.groq.com/openai/v1/chat/completions"),
            ({"base_url": "https://openrouter.ai/api"}, "https://openrouter.ai/api/v1/chat/completions"),
            ({"base_url": "https://example.com/v4", "path_style": "append_v1"}, "https://example.com/v4/v1/chat/completions"),
            ({"base_url": "https://example.com/v4", "paths": {"chat": "/custom"}}, "https://example.com/v4/custom"),
        ]
        for options, expected in cases:
            with self.subTest(options=options):
                adapter = OpenAiCompatibleAdapter({"id": "test", "options": options})
                self.assertEqual(adapter.request_body(request, "hello")[0], expected)

    def test_local_models_uses_versioned_base(self) -> None:
        seen = []

        def opener(request, timeout=None):
            seen.append(request.full_url)
            return io.BytesIO(json.dumps({"data": [{"id": "model-a"}]}).encode())

        self.assertEqual(foreman_deploy.local_models("https://example.com/openai/v1/", opener=opener), ["model-a"])
        self.assertEqual(seen, ["https://example.com/openai/v1/models"])

    def test_local_models_path_style_root(self) -> None:
        seen = []

        def opener(request, timeout=None):
            seen.append(request.full_url)
            return io.BytesIO(json.dumps({"data": [{"id": "model-a"}]}).encode())

        self.assertEqual(foreman_deploy.local_models("https://example.com/openai", opener=opener, path_style="root"), ["model-a"])
        self.assertEqual(seen, ["https://example.com/openai/models"])

    def test_endpoint_entry_path_options(self) -> None:
        base = endpoint_entry("test", base_url="https://example.com", model="m", classes=["fast"])
        self.assertNotIn("path_style", base["options"])
        self.assertNotIn("paths", base["options"])
        entry = endpoint_entry("test", base_url="https://example.com", model="m", classes=["fast"],
                               path_style="root", paths={"chat": "/custom"})
        self.assertEqual(entry["options"]["path_style"], "root")
        self.assertEqual(entry["options"]["paths"], {"chat": "/custom"})

    def test_endpoint_entry_rejects_invalid_path_style(self) -> None:
        with self.assertRaisesRegex(ValueError, "path_style"):
            endpoint_entry("test", base_url="https://example.com", model="m", classes=["fast"], path_style="bogus")

    def test_agent_entry_base_url(self) -> None:
        def entry(base_url: str) -> dict:
            state = {"provider_id": "gpu", "id": "s", "base_url": base_url,
                     "model": {"repo": "x/y", "model_type": "qwen2", "agent": True}}
            return foreman_deploy.agent_entry(state)["options"]["extra_config"]["model_providers.agentosgpu.base_url"]

        self.assertEqual(entry("https://abc-8000.proxy.runpod.net"), "https://abc-8000.proxy.runpod.net/v1")
        self.assertEqual(entry("https://example.com/v1"), "https://example.com/v1")

    def test_registry_entry_rejects_invalid_base(self) -> None:
        with self.assertRaisesRegex(ValueError, "credentials"):
            endpoint_entry("test", base_url="https://user:pass@example.com", model="m", classes=["fast"])


if __name__ == "__main__":
    unittest.main()
