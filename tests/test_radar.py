"""IMP-0015 Research Radar v1: Hub normalization, catalog merge, eval queue."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import radar  # noqa: E402


def hub_row(model_id: str, sha: str = "a" * 40, pipeline: str = "text-generation", downloads: int = 50_000, tags: list | None = None, **extra) -> dict:
    return {"id": model_id, "sha": sha, "pipeline_tag": pipeline, "downloads": downloads, "likes": 3,
            "tags": tags if tags is not None else ["license:apache-2.0", "base_model:org/base"], **extra}


class FakeHub:
    def __init__(self, pages: list) -> None:
        self.pages, self.urls = list(pages), []

    def __call__(self, request, timeout=None):
        self.urls.append(request.full_url)
        page = self.pages.pop(0)
        if isinstance(page, Exception):
            raise page
        return io.BytesIO(json.dumps(page).encode())


class NormalizeTests(unittest.TestCase):
    def test_modalities_license_refusal_and_quantization(self) -> None:
        row = hub_row("x/Model-abliterated-GGUF", tags=["gguf", "abliterated", "4-bit", "license:mit", "base_model:org/base", "base_model:quantized:org/base"])
        model = radar.normalize(row, "s", "t")
        self.assertEqual((model["license"], model["base_model"], model["refusal_profile_hint"], model["quantization"]), ("mit", "org/base", "abliterated", ["4-bit", "gguf"]))
        self.assertEqual((model["modalities"], model["revision"], model["provenance"]["url"]), (["text", "code"], "a" * 40, "https://huggingface.co/x/Model-abliterated-GGUF"))
        tts = radar.normalize(hub_row("y/tts", pipeline="text-to-speech", tags=["uncensored"], cardData={"license": "apache-2.0"}, safetensors={"total": 82_000_000}), "s", "t")
        self.assertEqual((tts["modalities"], tts["capabilities"], tts["refusal_profile_hint"], tts["license"], tts["parameters"]), (["audio"], ["tts"], "low", "apache-2.0", 82_000_000))
        self.assertIsNone(radar.normalize({"tags": []}, "s", "t"))

    def test_scan_url_expands_metadata(self) -> None:
        url = radar.scan_url({"search": "abliterated", "pipeline_tag": "text-to-image", "sort": "downloads", "limit": 5})
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual((query["search"], query["pipeline_tag"], query["limit"]), (["abliterated"], ["text-to-image"], ["5"]))
        self.assertIn("safetensors", query["expand[]"])


class ScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def queue(self) -> list[dict]:
        path = radar.queue_path(self.home)
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def test_new_models_revisions_and_queue_criteria(self) -> None:
        first = FakeHub([[hub_row("a/popular"), hub_row("b/unlicensed", tags=[]), hub_row("c/niche", downloads=10)]])
        result = radar.scan([{"name": "s"}], home=self.home, opener=first, pause=0)
        self.assertEqual((sorted(result["new"]), result["queued_for_eval"]), (["a/popular", "b/unlicensed", "c/niche"], ["a/popular"]))
        self.assertEqual(self.queue()[0]["suggested_suites"], ["EVS-CAPABILITY-CLASSIFICATION", "EVS-CONTEXT", "EVS-TEST-SELECTION"])
        second = FakeHub([[hub_row("a/popular", sha="b" * 40), hub_row("c/niche", downloads=10)]])
        again = radar.scan([{"name": "s"}], home=self.home, opener=second, pause=0)
        self.assertEqual((again["new"], again["new_revisions"], again["queued_for_eval"]), ([], ["a/popular"], ["a/popular"]))
        catalog = json.loads(radar.catalog_path(self.home).read_text(encoding="utf-8"))
        self.assertEqual(catalog["models"]["a/popular"]["revision"], "b" * 40)
        self.assertEqual(len(self.queue()), 2)

    def test_scan_errors_are_reported_not_raised(self) -> None:
        hub = FakeHub([OSError("offline"), [hub_row("a/x")]])
        result = radar.scan([{"name": "down"}, {"name": "up"}], home=self.home, opener=hub, pause=0, queue=False)
        self.assertEqual((result["errors"][0]["scan"], result["new"], self.queue()), ("down", ["a/x"], []))

    def test_catalog_filters(self) -> None:
        hub = FakeHub([[hub_row("a/abl", tags=["abliterated", "license:mit"], downloads=5), hub_row("b/asr", pipeline="automatic-speech-recognition", downloads=9)]])
        radar.scan([{"name": "s"}], home=self.home, opener=hub, pause=0, queue=False)
        self.assertEqual([m["model_id"] for m in radar.catalog_summary(self.home, modality="audio")["models"]], ["b/asr"])
        self.assertEqual([m["model_id"] for m in radar.catalog_summary(self.home, refusal_profile="abliterated")["models"]], ["a/abl"])
        self.assertEqual(radar.catalog_summary(Path(self.tmp.name) / "none")["catalog_size"], 0)


if __name__ == "__main__":
    unittest.main()
