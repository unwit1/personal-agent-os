"""IMP-0015: read-only Model & Compute view and its GUI API route."""

from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator_surfaces import SurfaceFixture  # noqa: E402

from agent_os.orchestrator import model_view, radar, refusal, throughput  # noqa: E402
from agent_os.orchestrator.compute import _cache_path  # noqa: E402
from agent_os.orchestrator.model_profile import endpoint_entry  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402
from agent_os.orchestrator.server import build_server  # noqa: E402
from agent_os.storage import write_json  # noqa: E402

GUI = Path(__file__).resolve().parents[1] / "gui"


class BuildTests(unittest.TestCase):
    def test_empty_home_renders_with_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            view = model_view.build(Path(tmp), registry=ProviderRegistry(providers=[]))
        self.assertEqual((view["providers"], view["catalog"]["size"], view["eval_queue"]["total"], view["throughput"]), ([], 0, 0, []))
        self.assertIn("compute inventory", view["inventory"]["note"])
        self.assertIn("read-only", view["note"])

    def test_populated_state_is_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            write_json(radar.catalog_path(home), {"models": {"org/abl": {"model_id": "org/abl", "pipeline": "text-generation", "license": "mit",
                                                                         "refusal_profile_hint": "abliterated", "downloads": 20000, "modalities": ["text"]}}})
            radar.queue_path(home).write_text(json.dumps({"model_id": "org/abl", "revision": "r", "status": "queued"}) + "\n", encoding="utf-8")
            write_json(_cache_path("runpod", home), {"fetched_at": "2026-09-29T00:00:00+00:00", "offers": [{"name": "A40", "vram_gb": 48, "tier": "secure", "usd_per_hour": 0.49}]})
            throughput.record(model="org/abl", gpu="A40", tokens_per_second=800, home=home)
            refusal.record(home, category="provider_policy", task_family="f", selection={"provider": "cloud", "model": "m"})
            registry = ProviderRegistry(providers=[endpoint_entry("local-abl", base_url="http://127.0.0.1:8000", model="org/abl", classes=["fast"], refusal_profile="abliterated")])
            view = model_view.build(home, registry=registry)
        self.assertEqual((view["providers"][0]["deployment"], view["providers"][0]["refusal_profile"]), ("local", "abliterated"))
        self.assertEqual([m["model_id"] for m in view["catalog"]["abliterated"]], ["org/abl"])
        self.assertEqual((view["eval_queue"]["by_status"], view["inventory"]["offers"][0]["name"], view["throughput"][0]["tokens_per_second"]), ({"queued": 1}, "A40", 800))
        self.assertEqual(view["refusals"]["events"], 1)

    def test_gui_panel_is_wired(self) -> None:
        html = (GUI / "index.html").read_text(encoding="utf-8")
        script = (GUI / "simple.js").read_text(encoding="utf-8")
        for element in ("compute-panel", "compute-providers", "compute-catalog", "compute-inventory", "compute-throughput", "compute-queue", "compute-signals"):
            self.assertIn(f'id="{element}"', html)
            self.assertIn(f'"{element}"', script)
        self.assertIn('api("model-compute")', script)


class ApiRouteTests(SurfaceFixture):
    def test_route_requires_token_and_returns_the_view(self) -> None:
        server, token = build_server("127.0.0.1", 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = server.server_address[1]

        def get(headers: dict) -> tuple[int, bytes]:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
            connection.request("GET", "/api/model-compute", headers={"Host": f"127.0.0.1:{port}", **headers})
            response = connection.getresponse()
            data = response.read()
            connection.close()
            return response.status, data

        self.assertEqual(get({})[0], 401)
        status, body = get({"X-Agent-OS-Token": token})
        self.assertEqual(status, 200, body)
        self.assertIn("eval_queue", json.loads(body))


if __name__ == "__main__":
    unittest.main()
