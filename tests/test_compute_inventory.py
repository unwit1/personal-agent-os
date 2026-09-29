"""IMP-0015 Phase 2 read-only slice: GPU inventory normalization, caching and quote options."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import compute, quote, secret_refs  # noqa: E402
from agent_os.orchestrator.workload import normalize_workload  # noqa: E402

PAYLOAD = {"data": {"gpuTypes": [
    {"id": "NVIDIA A100 80GB PCIe", "displayName": "A100 PCIe", "memoryInGb": 80, "securePrice": 1.59, "communityPrice": 1.19, "secureCloud": True, "communityCloud": True},
    {"id": "NVIDIA A40", "displayName": "A40", "memoryInGb": 48, "securePrice": 0.49, "communityPrice": 0.35, "secureCloud": True, "communityCloud": False},
    {"id": "X", "displayName": "Gone", "memoryInGb": 24, "securePrice": 0, "communityPrice": 0, "secureCloud": False, "communityCloud": False},
]}}


class FakeOpener:
    def __init__(self, payload: dict | None = None, error: Exception | None = None) -> None:
        self.payload, self.error, self.requests = payload, error, []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        if self.error:
            raise self.error
        return io.BytesIO(json.dumps(self.payload).encode())


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.object(secret_refs, "_keyring", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(secret_refs.env_var(compute.RUNPOD_SECRET), None)

    def test_normalize_drops_unoffered_tiers_and_sorts_by_price(self) -> None:
        offers = compute.normalize_runpod(PAYLOAD)
        self.assertEqual([(o["name"], o["tier"], o["usd_per_hour"]) for o in offers],
                         [("A40", "secure", 0.49), ("A100 PCIe", "community", 1.19), ("A100 PCIe", "secure", 1.59)])

    def test_live_then_cached_and_key_only_when_configured(self) -> None:
        opener = FakeOpener(PAYLOAD)
        first = compute.runpod_inventory(home=self.home, opener=opener, now=lambda: 1000.0)
        self.assertEqual((first["source"], first["authenticated"], len(first["offers"])), ("live", False, 3))
        self.assertNotIn("Authorization", opener.requests[0].headers)
        second = compute.runpod_inventory(home=self.home, opener=opener, now=lambda: 1000.0 + 60)
        self.assertEqual((second["source"], len(opener.requests)), ("cache", 1))
        expired = compute.runpod_inventory(home=self.home, opener=opener, now=lambda: 1000.0 + compute.CACHE_SECONDS + 1)
        self.assertEqual((expired["source"], len(opener.requests)), ("live", 2))
        with mock.patch.dict(os.environ, {secret_refs.env_var(compute.RUNPOD_SECRET): "rp-key"}):
            compute.runpod_inventory(home=self.home, opener=opener, refresh=True)
        self.assertEqual(opener.requests[-1].headers["Authorization"], "Bearer rp-key")

    def test_failures_degrade_to_an_empty_inventory(self) -> None:
        down = compute.runpod_inventory(home=self.home, opener=FakeOpener(error=OSError("offline")), refresh=True)
        self.assertEqual((down["offers"], down["error"].startswith("OSError")), ([], True))
        graphql = compute.runpod_inventory(home=self.home, opener=FakeOpener({"errors": [{"message": "bad"}]}), refresh=True)
        self.assertIn("bad", graphql["error"])
        with self.assertRaises(ValueError):
            compute.inventory("nowhere")


class GpuOptionTests(unittest.TestCase):
    offers = compute.normalize_runpod(PAYLOAD)

    def test_vram_floor_throughput_and_quote_integration(self) -> None:
        workload = normalize_workload({"type": "batch_inference", "resources": {"vram_gb": 80}, "size": {"input_tokens": 2000, "output_tokens": 800, "items": 20000}})
        self.assertEqual(compute.gpu_options(self.offers, workload), [])  # no throughput -> nothing priced
        options = compute.gpu_options(self.offers, workload, gen_tokens_per_second=1500)
        self.assertEqual([o["id"] for o in options], ["runpod:A100 PCIe:community", "runpod:A100 PCIe:secure"])
        api = {"kind": "api", "id": "api", "price_in_per_mtok": 3.0, "price_out_per_mtok": 15.0}
        result = quote.quote(workload, [api, *options])
        self.assertEqual(result["recommended"], "runpod:A100 PCIe:community")
        self.assertIn("api_vs_gpu", result)
        self.assertFalse(result["recommended_gate"]["allowed"])  # budget not approved

    def test_training_uses_train_throughput_and_tier_filter(self) -> None:
        workload = normalize_workload({"type": "adapter_training", "size": {"dataset_tokens": 1e7}})
        self.assertEqual(compute.gpu_options(self.offers, workload, gen_tokens_per_second=999), [])
        options = compute.gpu_options(self.offers, workload, train_tokens_per_second=3000, tiers=("secure",))
        self.assertTrue(all(o["id"].endswith(":secure") and o["train_tokens_per_second"] == 3000 for o in options))


if __name__ == "__main__":
    unittest.main()
