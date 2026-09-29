"""IMP-0015: workload contract, quote/budget engine and artifact manifests."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import artifacts, quote  # noqa: E402
from agent_os.orchestrator.workload import normalize_workload, to_requirements  # noqa: E402

API = {"kind": "api", "id": "api-mid", "price_in_per_mtok": 3.0, "price_out_per_mtok": 15.0, "failure_rate": 0.0}
POD = {"kind": "gpu_pod", "id": "pod-a100", "gpu_hourly_usd": 1.2, "gen_tokens_per_second": 1000, "train_tokens_per_second": 4000,
       "startup_minutes": 6, "idle_minutes": 0, "failure_rate": 0.0}
SERVERLESS = {"kind": "serverless", "id": "sls", "gpu_hourly_usd": 2.4, "gen_tokens_per_second": 1000, "startup_minutes": 0.5, "failure_rate": 0.0}


class WorkloadTests(unittest.TestCase):
    def test_modalities_beyond_text_need_no_schema_change(self) -> None:
        image = normalize_workload({"type": "inference", "modalities": ["image"], "capabilities": ["image_editing"], "size": {"images": 20}})
        audio = normalize_workload({"type": "batch_inference", "modality": "audio", "capabilities": ["asr", "diarization"], "size": {"audio_seconds": 3600}})
        self.assertEqual((image["modalities"], audio["modalities"], audio["size"]["audio_seconds"]), (["image"], ["audio"], 3600.0))
        self.assertEqual(audio["unrecognized_capabilities"], [])
        self.assertEqual(normalize_workload({"capabilities": ["telepathy"]})["unrecognized_capabilities"], ["telepathy"])

    def test_validation(self) -> None:
        for raw in ({"type": "dream"}, {"modalities": ["smell"]}, {"sensitivity": "top"}, {"size": {"items": -1}}, {"type": "adapter_training"}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_workload(raw)
        self.assertFalse(normalize_workload({"budget": {"approved": "yes"}})["budget"]["approved"])  # only literal true approves

    def test_sensitivity_sets_a_deployment_floor_that_explicit_requirements_only_narrow(self) -> None:
        self.assertEqual(to_requirements(normalize_workload({"sensitivity": "secret"}))["deployment"], ["local"])
        private = normalize_workload({"sensitivity": "private", "requirements": {"deployment": ["gpu_pod", "api"]}})
        self.assertEqual(to_requirements(private)["deployment"], ["gpu_pod"])
        with self.assertRaises(ValueError):
            to_requirements(normalize_workload({"sensitivity": "secret", "requirements": {"deployment": "api"}}))
        self.assertNotIn("deployment", to_requirements(normalize_workload({"sensitivity": "public"})))


class QuoteTests(unittest.TestCase):
    def test_api_cost_is_tokens_times_price_times_attempts(self) -> None:
        workload = normalize_workload({"size": {"input_tokens": 1_000_000, "output_tokens": 100_000, "items": 2}})
        option = quote.api_option(API, workload)
        self.assertEqual(option["cost_usd"]["expected"], round((2_000_000 * 3 + 200_000 * 15) / 1e6, 4))
        doubled = quote.api_option({**API, "failure_rate": 0.5}, workload)
        self.assertAlmostEqual(doubled["cost_usd"]["expected"], 2 * option["cost_usd"]["expected"], places=3)

    def test_small_jobs_prefer_api_large_batches_prefer_gpu(self) -> None:
        small = quote.quote(normalize_workload({"size": {"input_tokens": 2000, "output_tokens": 500}}), [API, POD])
        self.assertEqual(small["recommended"], "api-mid")
        big = quote.quote(normalize_workload({"type": "batch_inference", "size": {"input_tokens": 2000, "output_tokens": 1000, "items": 50_000}}), [API, POD, SERVERLESS])
        self.assertEqual(big["recommended"], "pod-a100")
        self.assertGreater(big["api_vs_gpu"]["gpu_saving_usd_expected"], 0)
        pod = next(item for item in big["options"] if item["id"] == "pod-a100")
        self.assertLess(pod["cost_usd"]["low"], pod["cost_usd"]["expected"])
        self.assertLess(pod["cost_usd"]["expected"], pod["cost_usd"]["high"])

    def test_training_quote_has_bands(self) -> None:
        workload = normalize_workload({"type": "adapter_training", "size": {"dataset_tokens": 50_000_000, "epochs": 2}})
        option = quote.gpu_option(POD, workload)
        expected_hours = 100_000_000 / 4000 / 3600 + 6 / 60
        self.assertAlmostEqual(option["billed_hours"]["expected"], round(expected_hours, 4), places=3)
        self.assertAlmostEqual(option["cost_usd"]["expected"], round(expected_hours * 1.2, 4), places=2)

    def test_budget_gate_never_allows_unapproved_or_over_cap_spend(self) -> None:
        base = {"size": {"input_tokens": 1_000_000, "output_tokens": 1_000_000}}
        unapproved = quote.quote(normalize_workload(base), [API])["recommended_gate"]
        self.assertEqual((unapproved["allowed"], unapproved["requires_approval"]), (False, True))
        no_cap = quote.quote(normalize_workload({**base, "budget": {"approved": True}}), [API])["recommended_gate"]
        self.assertIn("no job hard cap", no_cap["reason"])
        over = quote.quote(normalize_workload({**base, "budget": {"approved": True, "job_hard_cap_usd": 1}}), [API])["recommended_gate"]
        self.assertIn("exceeds job hard cap", over["reason"])
        project = quote.quote(normalize_workload({**base, "budget": {"approved": True, "job_hard_cap_usd": 100, "project_usd": 5}}), [API])["recommended_gate"]
        self.assertIn("project budget", project["reason"])
        ok = quote.quote(normalize_workload({**base, "budget": {"approved": True, "job_hard_cap_usd": 100}}), [API])["recommended_gate"]
        self.assertTrue(ok["allowed"])
        self.assertTrue(quote.budget_gate(0, normalize_workload({}))["allowed"])

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            quote.quote(normalize_workload({}), [])
        with self.assertRaises(ValueError):
            quote.gpu_option({**POD, "gen_tokens_per_second": 0}, normalize_workload({}))


class ArtifactTests(unittest.TestCase):
    def test_manifest_identity_and_validation(self) -> None:
        adapter = artifacts.build("adapter", "runpod://volume/lora-1", base_model="org/base", base_revision="abc123", training_config={"r": 16, "lr": 2e-4}, job_id="J1")
        again = artifacts.build("adapter", "runpod://volume/lora-1", base_model="org/base", base_revision="abc123", training_config={"lr": 2e-4, "r": 16}, job_id="J1")
        self.assertEqual(adapter["id"], again["id"])
        self.assertTrue(adapter["id"].startswith("ART-"))
        for kwargs in ({"kind": "blob"}, {"kind": "checkpoint"}, {"kind": "output", "sha256": "xyz"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                artifacts.build(kwargs.pop("kind"), "file://x", **kwargs)

    def test_verify_and_latest_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ckpt.bin"
            path.write_bytes(b"weights")
            good = artifacts.build("checkpoint", path.as_uri(), sha256=hashlib.sha256(b"weights").hexdigest(), size_bytes=7, base_model="b", base_revision="r", job_id="J", step=100)
            self.assertTrue(artifacts.verify(good, path)["ok"])
            path.write_bytes(b"weightz")
            self.assertEqual(artifacts.verify(good, path)["reason"], "sha256 mismatch")
            self.assertEqual(artifacts.verify({"sha256": None}, path)["reason"], "manifest has no sha256")
            later = artifacts.build("checkpoint", "file://c2", base_model="b", base_revision="r", job_id="J", step=200)
            other = artifacts.build("checkpoint", "file://c3", base_model="b", base_revision="r", job_id="K", step=900)
            self.assertEqual(artifacts.latest_resumable([good, later, other], "J")["step"], 200)
            self.assertIsNone(artifacts.latest_resumable([other], "J"))


if __name__ == "__main__":
    unittest.main()
