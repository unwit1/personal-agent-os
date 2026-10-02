"""pod_request throughput flags and weight-volume options (IMP-0015)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator import budget, foreman_deploy as fd  # noqa: E402

from test_foreman_deploy import HF_CONFIG, HF_INFO, OFFERS, Base  # noqa: E402

H100 = {"provider": "runpod", "gpu_id": "NVIDIA H100 80GB HBM3", "name": "H100", "vram_gb": 80, "tier": "secure", "gpu_count": 1, "hourly_usd": 2.5}
A5000 = {**OFFERS[1], "gpu_count": 1, "hourly_usd": 0.5}


def _flag(args: list[str], name: str) -> str:
    return args[args.index(name) + 1]


class PodRequestTuningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = fd.summarize_info(HF_INFO, HF_CONFIG)

    def test_throughput_flags_present_after_existing_flags(self) -> None:
        args = fd.pod_request(self.model, A5000, "k", None, "n")["dockerStartCmd"]
        self.assertIn("--enable-prefix-caching", args)
        self.assertIn("--enable-chunked-prefill", args)
        self.assertGreaterEqual(int(_flag(args, "--max-num-seqs")), 4)
        self.assertEqual(_flag(args, "--gpu-memory-utilization"), "0.90")
        self.assertLess(args.index("--tensor-parallel-size"), args.index("--enable-prefix-caching"))
        self.assertNotIn("--kv-cache-dtype", args)  # A5000 has no fp8 KV support

    def test_fp8_kv_cache_on_h100(self) -> None:
        args = fd.pod_request(self.model, H100, "k", None, "n")["dockerStartCmd"]
        self.assertEqual(_flag(args, "--kv-cache-dtype"), "fp8")

    def test_overrides_are_honoured(self) -> None:
        body = fd.pod_request(self.model, H100, "k", None, "n", vllm_overrides={
            "gpu_memory_utilization": 0.8, "max_num_seqs": 7, "prefix_caching": False, "kv_cache_dtype": None})
        args = body["dockerStartCmd"]
        self.assertEqual(_flag(args, "--gpu-memory-utilization"), "0.8")
        self.assertEqual(_flag(args, "--max-num-seqs"), "7")
        self.assertNotIn("--enable-prefix-caching", args)
        self.assertIn("--enable-chunked-prefill", args)
        self.assertNotIn("--kv-cache-dtype", args)

    def test_lower_utilization_shrinks_computed_max_num_seqs(self) -> None:
        model = {**self.model, "kv_bytes_per_token": 200000, "weight_gb": 10}
        base = int(_flag(fd.pod_request(model, H100, "k", None, "n")["dockerStartCmd"], "--max-num-seqs"))
        low = int(_flag(fd.pod_request(model, H100, "k", None, "n", vllm_overrides={"gpu_memory_utilization": 0.5})["dockerStartCmd"], "--max-num-seqs"))
        self.assertLess(low, base)

    def test_choice_without_vram_falls_back_to_floor(self) -> None:
        args = fd.pod_request(self.model, {"gpu_id": "g", "gpu_count": 1, "tier": "community"}, "k", None, "n")["dockerStartCmd"]
        self.assertEqual(_flag(args, "--max-num-seqs"), "4")

    def test_volume_fields_only_when_requested(self) -> None:
        plain = fd.pod_request(self.model, A5000, "k", "hf", "n")
        self.assertEqual(plain["volumeInGb"], 0)
        self.assertNotIn("networkVolumeId", plain)
        self.assertNotIn("HF_HOME", plain["env"])
        cached = fd.pod_request({**self.model, "gated": True}, A5000, "k", "hf", "n", weight_volume="vol123")
        self.assertEqual(cached["networkVolumeId"], "vol123")
        self.assertEqual(cached["volumeMountPath"], "/runpod-volume")
        self.assertEqual(cached["volumeInGb"], 0)
        self.assertEqual(cached["env"]["HF_HOME"], "/runpod-volume/hf")
        self.assertEqual(cached["env"]["VLLM_API_KEY"], "k")
        self.assertEqual(cached["env"]["HF_TOKEN"], "hf")


class DeployThreadingTests(Base):
    def test_deploy_threads_options_into_pod_and_state(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        self.manager().deploy("org/coder-7b", job_cap_usd=1.0, background=False,
                              vllm_overrides={"max_num_seqs": 9}, weight_volume="vol9")
        body = self.cloud.created[0]
        self.assertEqual(_flag(body["dockerStartCmd"], "--max-num-seqs"), "9")
        self.assertEqual(body["networkVolumeId"], "vol9")
        state = fd.load_state(self.foreman_home)
        self.assertEqual(state["vllm_overrides"], {"max_num_seqs": 9})
        self.assertEqual(state["weight_volume"], "vol9")


if __name__ == "__main__":
    unittest.main()
