"""Tests for vLLM throughput tuning."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import vllm_tuning  # noqa: E402


class FP8SupportedTests(unittest.TestCase):
    def test_h100_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("nvidia-h100-pcie"))

    def test_h200_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("nvidia-h200-sxm5"))

    def test_h20_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("nvidia-h20-sxm"))

    def test_l4_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("nvidia-l4"))

    def test_l40_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("nvidia-l40-sxm"))

    def test_rtx_4090_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("rtx-4090"))

    def test_rtx_6000_ada_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("rtx-6000-ada"))

    def test_b200_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("nvidia-b200"))

    def test_rtx_5090_supports_fp8(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("RTX-5090"))

    def test_a100_does_not_support_fp8(self) -> None:
        self.assertFalse(vllm_tuning.fp8_kv_supported("nvidia-a100-pcie"))

    def test_a100_sxm_does_not_support_fp8(self) -> None:
        self.assertFalse(vllm_tuning.fp8_kv_supported("nvidia-a100-sxm"))

    def test_case_insensitive(self) -> None:
        self.assertTrue(vllm_tuning.fp8_kv_supported("NVIDIA-H100-PCIE"))
        self.assertTrue(vllm_tuning.fp8_kv_supported("Nvidia-L4"))

    def test_empty_string_not_supported(self) -> None:
        self.assertFalse(vllm_tuning.fp8_kv_supported(""))

    def test_none_not_supported(self) -> None:
        self.assertFalse(vllm_tuning.fp8_kv_supported(None))


class MaxNumSeqsTests(unittest.TestCase):
    def test_missing_kv_bytes_per_token_returns_floor(self) -> None:
        model = {"weight_gb": 14.0}
        result = vllm_tuning.max_num_seqs(model, 1, 80.0)
        self.assertEqual(result, 4)

    def test_missing_weight_gb_returns_floor(self) -> None:
        model = {"kv_bytes_per_token": 3200}
        result = vllm_tuning.max_num_seqs(model, 1, 80.0)
        self.assertEqual(result, 4)

    def test_negative_headroom_returns_floor(self) -> None:
        # Very small VRAM, large weights: headroom is negative
        model = {"kv_bytes_per_token": 3200, "weight_gb": 100.0}
        result = vllm_tuning.max_num_seqs(model, 1, 80.0)
        self.assertEqual(result, 4)

    def test_zero_headroom_returns_floor(self) -> None:
        # VRAM exactly matches weight overhead
        model = {"kv_bytes_per_token": 3200, "weight_gb": 80.0 / 1.1}
        result = vllm_tuning.max_num_seqs(model, 1, 80.0)
        self.assertEqual(result, 4)

    def test_grows_with_vram(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        # 20 GB
        result_20 = vllm_tuning.max_num_seqs(model, 1, 20.0)
        # 30 GB
        result_30 = vllm_tuning.max_num_seqs(model, 1, 30.0)
        self.assertGreater(result_30, result_20)

    def test_grows_with_gpu_count(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        # 1x 20 GB
        result_1 = vllm_tuning.max_num_seqs(model, 1, 20.0)
        # 2x 20 GB
        result_2 = vllm_tuning.max_num_seqs(model, 2, 20.0)
        self.assertGreater(result_2, result_1)

    def test_grows_with_fp8(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        # 2-byte KV (default)
        result_bf16 = vllm_tuning.max_num_seqs(model, 1, 20.0, kv_dtype_bytes=2)
        # 1-byte KV (fp8)
        result_fp8 = vllm_tuning.max_num_seqs(model, 1, 20.0, kv_dtype_bytes=1)
        self.assertGreater(result_fp8, result_bf16)

    def test_clamped_at_floor(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        # With floor=10, even a very small amount of headroom
        result = vllm_tuning.max_num_seqs(model, 1, 80.0, floor=10)
        self.assertGreaterEqual(result, 10)

    def test_clamped_at_ceiling(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 1.0}
        # With ceiling=20, even large headroom won't exceed it
        result = vllm_tuning.max_num_seqs(model, 8, 80.0, ceiling=20)
        self.assertLessEqual(result, 20)

    def test_respects_custom_context(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        # Small context should yield more concurrent sequences
        result_small = vllm_tuning.max_num_seqs(model, 1, 40.0, context=8192)
        # Large context should yield fewer concurrent sequences
        result_large = vllm_tuning.max_num_seqs(model, 1, 40.0, context=131072)
        self.assertGreater(result_small, result_large)

    def test_respects_memory_utilization(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        # 90% utilization (default)
        result_90 = vllm_tuning.max_num_seqs(model, 1, 20.0, gpu_memory_utilization=0.90)
        # 80% utilization (more conservative)
        result_80 = vllm_tuning.max_num_seqs(model, 1, 20.0, gpu_memory_utilization=0.80)
        self.assertGreater(result_90, result_80)

    def test_realistic_values(self) -> None:
        # Qwen2.5-14B-like: 3200 bytes/token for context window
        model = {"kv_bytes_per_token": 3200, "weight_gb": 28.0}
        result = vllm_tuning.max_num_seqs(model, 1, 50.0)
        # Should be a reasonable number: at least 4, at most the ceiling of 256
        self.assertGreaterEqual(result, 4)
        self.assertLessEqual(result, 256)


class ThroughputArgsTests(unittest.TestCase):
    def test_default_flags_present(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice)

        self.assertIn("--enable-prefix-caching", args)
        self.assertIn("--enable-chunked-prefill", args)
        self.assertIn("--max-num-seqs", args)
        # A100 doesn't support fp8, so no --kv-cache-dtype
        self.assertNotIn("--kv-cache-dtype", args)

    def test_fp8_on_h100(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-h100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice)

        self.assertIn("--enable-prefix-caching", args)
        self.assertIn("--enable-chunked-prefill", args)
        self.assertIn("--max-num-seqs", args)
        self.assertIn("--kv-cache-dtype", args)
        fp8_idx = args.index("--kv-cache-dtype")
        self.assertEqual(args[fp8_idx + 1], "fp8")

    def test_no_fp8_on_a100(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice)

        self.assertNotIn("--kv-cache-dtype", args)

    def test_override_prefix_caching_false(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice, overrides={"prefix_caching": False})

        self.assertNotIn("--enable-prefix-caching", args)
        self.assertIn("--enable-chunked-prefill", args)

    def test_override_chunked_prefill_false(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice, overrides={"chunked_prefill": False})

        self.assertIn("--enable-prefix-caching", args)
        self.assertNotIn("--enable-chunked-prefill", args)

    def test_override_max_num_seqs(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice, overrides={"max_num_seqs": 16})

        seqs_idx = args.index("--max-num-seqs")
        self.assertEqual(args[seqs_idx + 1], "16")

    def test_override_max_num_seqs_false_removes_flag(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice, overrides={"max_num_seqs": False})

        self.assertNotIn("--max-num-seqs", args)

    def test_override_kv_cache_dtype_none_removes_flag(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-h100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice, overrides={"kv_cache_dtype": None})

        self.assertNotIn("--kv-cache-dtype", args)

    def test_override_kv_cache_dtype_custom_value(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice, overrides={"kv_cache_dtype": "fp16"})

        dtype_idx = args.index("--kv-cache-dtype")
        self.assertEqual(args[dtype_idx + 1], "fp16")

    def test_all_overrides_honored(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-h100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(
            model,
            choice,
            overrides={
                "prefix_caching": False,
                "chunked_prefill": False,
                "max_num_seqs": 32,
                "kv_cache_dtype": "fp8_e5m2",
            },
        )

        self.assertNotIn("--enable-prefix-caching", args)
        self.assertNotIn("--enable-chunked-prefill", args)
        seqs_idx = args.index("--max-num-seqs")
        self.assertEqual(args[seqs_idx + 1], "32")
        dtype_idx = args.index("--kv-cache-dtype")
        self.assertEqual(args[dtype_idx + 1], "fp8_e5m2")

    def test_empty_overrides_dict(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args1 = vllm_tuning.throughput_args(model, choice)
        args2 = vllm_tuning.throughput_args(model, choice, overrides={})

        self.assertEqual(args1, args2)

    def test_max_num_seqs_calculated_with_fp8_on_h100(self) -> None:
        """When H100 is detected, max_num_seqs should use fp8 scaling."""
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-h100-pcie", "gpu_count": 1, "vram_gb": 20.0}
        args = vllm_tuning.throughput_args(model, choice)

        # Should have computed max_num_seqs with fp8 (kv_dtype_bytes=1)
        # which yields larger value than bf16 (kv_dtype_bytes=2)
        seqs_idx = args.index("--max-num-seqs")
        h100_seqs = int(args[seqs_idx + 1])

        # Compare with A100 calculation (no fp8)
        choice_a100 = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 20.0}
        args_a100 = vllm_tuning.throughput_args(model, choice_a100)
        seqs_idx_a100 = args_a100.index("--max-num-seqs")
        a100_seqs = int(args_a100[seqs_idx_a100 + 1])

        self.assertGreater(h100_seqs, a100_seqs)

    def test_h100_with_kv_cache_dtype_none_override(self) -> None:
        """H100 with kv_cache_dtype=None override should not use fp8 scaling, matching A100."""
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-h100-pcie", "gpu_count": 1, "vram_gb": 20.0}
        # Override to disable fp8, even though H100 supports it
        args_h100_no_fp8 = vllm_tuning.throughput_args(model, choice, overrides={"kv_cache_dtype": None})

        # Compare with A100 (which also has no fp8)
        choice_a100 = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 20.0}
        args_a100 = vllm_tuning.throughput_args(model, choice_a100)

        # Extract max_num_seqs from both
        seqs_idx_h100 = args_h100_no_fp8.index("--max-num-seqs")
        h100_seqs = int(args_h100_no_fp8[seqs_idx_h100 + 1])

        seqs_idx_a100 = args_a100.index("--max-num-seqs")
        a100_seqs = int(args_a100[seqs_idx_a100 + 1])

        # Should be the same
        self.assertEqual(h100_seqs, a100_seqs)
        # And kv_cache_dtype should not be in args
        self.assertNotIn("--kv-cache-dtype", args_h100_no_fp8)


class EdgeCasesTests(unittest.TestCase):
    def test_context_from_model_metadata(self) -> None:
        """throughput_args should pass model.get('context') to max_num_seqs."""
        model = {
            "kv_bytes_per_token": 3200,
            "weight_gb": 14.0,
            "context": 8192,  # Smaller context than default 32768
        }
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 20.0}
        args = vllm_tuning.throughput_args(model, choice)

        # With smaller context (8192 vs 32768), should get higher max_num_seqs
        seqs_idx = args.index("--max-num-seqs")
        seqs_with_custom_context = int(args[seqs_idx + 1])

        # Compare with default context
        model_default_context = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        args_default = vllm_tuning.throughput_args(model_default_context, choice)
        seqs_idx_default = args_default.index("--max-num-seqs")
        seqs_with_default_context = int(args_default[seqs_idx_default + 1])

        # Smaller context should allow more concurrent sequences
        self.assertGreater(seqs_with_custom_context, seqs_with_default_context)

    def test_missing_choice_fields_handled(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": None}  # Missing gpu_count, vram_gb
        args = vllm_tuning.throughput_args(model, choice)
        # Should still generate args (with defaults)
        self.assertIn("--enable-prefix-caching", args)

    def test_model_with_extra_fields(self) -> None:
        model = {
            "kv_bytes_per_token": 3200,
            "weight_gb": 14.0,
            "repo": "Qwen/Qwen2.5-14B",
            "params": 14e9,
            "context": 32768,
        }
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        args = vllm_tuning.throughput_args(model, choice)
        self.assertIn("--enable-prefix-caching", args)

    def test_very_large_vram(self) -> None:
        model = {"kv_bytes_per_token": 3200, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-h100-pcie", "gpu_count": 8, "vram_gb": 141.0}
        result = vllm_tuning.max_num_seqs(model, choice["gpu_count"], choice["vram_gb"])
        # Should be clamped at ceiling
        self.assertLessEqual(result, 256)

    def test_very_small_kv_bytes_per_token(self) -> None:
        model = {"kv_bytes_per_token": 64, "weight_gb": 14.0}
        choice = {"gpu_id": "nvidia-a100-pcie", "gpu_count": 1, "vram_gb": 80.0}
        result = vllm_tuning.max_num_seqs(model, 1, 80.0)
        # Should still be reasonable
        self.assertGreaterEqual(result, 4)


if __name__ == "__main__":
    unittest.main()
