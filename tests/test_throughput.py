"""IMP-0015: serving-throughput evidence, endpoint measurement and quote integration."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import compute, throughput  # noqa: E402
from agent_os.orchestrator.workload import normalize_workload  # noqa: E402


class FakeOpenAI(BaseHTTPRequestHandler):
    """OpenAI-compatible stub: 100 completion tokens after a short delay."""

    seen: list[dict] = []

    def do_POST(self) -> None:  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        FakeOpenAI.seen.append(body)
        time.sleep(0.05)
        payload = json.dumps({"model": body["model"], "choices": [{"message": {"content": "x"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 100}}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args) -> None:
        pass


class RecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_validation(self) -> None:
        for kwargs in ({"model": "", "gpu": "A40", "tokens_per_second": 5}, {"model": "m", "gpu": "A40", "tokens_per_second": 0},
                       {"model": "m", "gpu": "A40", "tokens_per_second": 5, "kind": "vibes"}, {"model": "m", "gpu": "A40", "tokens_per_second": 5, "source": "rumor"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                throughput.record(home=self.home, **kwargs)

    def test_best_prefers_measured_then_newest_and_lookup_matches_offers(self) -> None:
        throughput.record(model="org/M", gpu="A100 PCIe", tokens_per_second=900, source="assumed", home=self.home)
        throughput.record(model="org/M", gpu="A100 PCIe", tokens_per_second=1200, source="measured", home=self.home)
        time.sleep(1.1)
        throughput.record(model="org/M", gpu="A100 PCIe", tokens_per_second=1300, source="measured", home=self.home)
        throughput.record(model="org/M", gpu="A100 PCIe", tokens_per_second=4000, kind="training", home=self.home)
        self.assertEqual(throughput.best("org/m", "a100-pcie", home=self.home)["tokens_per_second"], 1300)
        self.assertEqual(throughput.best("org/M", kind="training", home=self.home)["tokens_per_second"], 4000)
        self.assertIsNone(throughput.best("org/M", "H100", home=self.home))
        rate = throughput.lookup("org/M", home=self.home)
        self.assertEqual((rate({"name": "A100 PCIe", "gpu_id": "NVIDIA A100 80GB PCIe"}), rate({"name": "A40", "gpu_id": "NVIDIA A40"})), (1300.0, None))

    def test_gpu_options_price_only_offers_with_evidence(self) -> None:
        throughput.record(model="org/M", gpu="A100 PCIe", tokens_per_second=1500, home=self.home)
        offers = [{"provider": "runpod", "gpu_id": "a40", "name": "A40", "vram_gb": 48, "tier": "secure", "usd_per_hour": 0.49},
                  {"provider": "runpod", "gpu_id": "a100", "name": "A100 PCIe", "vram_gb": 80, "tier": "community", "usd_per_hour": 1.19}]
        workload = normalize_workload({"size": {"output_tokens": 100}})
        options = compute.gpu_options(offers, workload, rate_for=throughput.lookup("org/M", home=self.home))
        self.assertEqual([(o["id"], o["gen_tokens_per_second"], o["throughput_source"]) for o in options], [("runpod:A100 PCIe:community", 1500.0, "measured")])
        explicit = compute.gpu_options(offers, workload, gen_tokens_per_second=700)
        self.assertEqual({o["throughput_source"] for o in explicit}, {"explicit"})


class MeasureTests(unittest.TestCase):
    def test_measures_aggregate_tokens_per_second_against_a_real_http_endpoint(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOpenAI)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        FakeOpenAI.seen = []
        provider = {"id": "local", "options": {"base_url": f"http://127.0.0.1:{server.server_address[1]}"}}
        result = throughput.measure(provider, "org/M", requests=6, concurrency=3, max_tokens=64)
        self.assertEqual((result["succeeded"], result["completion_tokens"], result["errors"]), (6, 600, []))
        self.assertGreater(result["tokens_per_second"], result["per_request_tps"])  # concurrency helps aggregate throughput
        self.assertEqual({(body["max_tokens"], body["temperature"], body["model"]) for body in FakeOpenAI.seen}, {(64, 0, "org/M")})

    def test_unreachable_endpoint_reports_errors(self) -> None:
        result = throughput.measure({"id": "down", "options": {"base_url": "http://127.0.0.1:9", "max_attempts": 1}}, "m", requests=2, concurrency=2, timeout=2)
        self.assertEqual((result["succeeded"], result["tokens_per_second"]), (0, None))
        self.assertTrue(result["errors"])
        with self.assertRaises(ValueError):
            throughput.measure({"id": "x", "options": {}}, "m", requests=0)


if __name__ == "__main__":
    unittest.main()
