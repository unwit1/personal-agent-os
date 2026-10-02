"""Weight cache cost analysis and RunPod volume integration."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import weight_cache  # noqa: E402


class WeightCacheTests(unittest.TestCase):
    def test_large_model_many_starts_recommended(self) -> None:
        # Large model (700GB), expensive pod ($8/hr), frequent restarts (30/mo) -> cache pays off.
        result = weight_cache.cost_check(
            weight_gb=700,
            hourly_usd=8.0,
            starts_per_month=30,
        )
        self.assertEqual(result["volume_gb"], 840)  # ceil(700 * 1.2)
        self.assertAlmostEqual(result["storage_usd_month"], 840 * 0.07, places=2)
        self.assertAlmostEqual(result["download_minutes_per_start"], 700 / 0.5 / 60, places=1)
        # download_usd_month = 30 * (700 / 0.5 / 3600) * 8.0
        self.assertAlmostEqual(result["download_usd_month"], 30 * (700 / 0.5 / 3600) * 8.0, places=2)
        self.assertGreater(result["saves_usd_month"], 0)
        self.assertTrue(result["recommended"])

    def test_small_model_few_starts_not_recommended(self) -> None:
        # Small model (3GB), cheap pod ($0.10/hr), rare restarts (1/mo) -> cache is not worth it.
        result = weight_cache.cost_check(
            weight_gb=3,
            hourly_usd=0.10,
            starts_per_month=1,
        )
        self.assertEqual(result["volume_gb"], 4)  # ceil(3 * 1.2)
        self.assertAlmostEqual(result["storage_usd_month"], 4 * 0.07, places=2)
        self.assertAlmostEqual(result["download_minutes_per_start"], 3 / 0.5 / 60, places=2)
        # download_usd_month = 1 * (3 / 0.5 / 3600) * 0.10
        self.assertAlmostEqual(result["download_usd_month"], 1 * (3 / 0.5 / 3600) * 0.10, places=4)
        self.assertLess(result["saves_usd_month"], 0)
        self.assertFalse(result["recommended"])

    def test_arithmetic_downloads_per_start(self) -> None:
        # 100 GB at 1 GB/s should take 100 seconds = 100/60 minutes.
        result = weight_cache.cost_check(
            weight_gb=100,
            hourly_usd=1.0,
            starts_per_month=1,
            download_gbps=1.0,
        )
        self.assertAlmostEqual(result["download_minutes_per_start"], 100 / 60, places=2)

    def test_arithmetic_monthly_download_cost(self) -> None:
        # 50 GB, $1/hr, 10 restarts/mo, 1 GB/s -> 50*10 seconds = 500 seconds = 500/3600 hours
        # cost = 500/3600 * 1.0 = $0.139
        result = weight_cache.cost_check(
            weight_gb=50,
            hourly_usd=1.0,
            starts_per_month=10,
            download_gbps=1.0,
        )
        self.assertAlmostEqual(result["download_usd_month"], 500 / 3600 * 1.0, places=4)

    def test_custom_storage_price_affects_recommendation(self) -> None:
        # Medium model, multiple starts/mo, expensive pod: cheap storage makes it worthwhile.
        result = weight_cache.cost_check(
            weight_gb=20,
            hourly_usd=5.0,
            starts_per_month=10,
            usd_per_gb_month=0.01,
        )
        self.assertGreater(result["saves_usd_month"], 0)
        self.assertTrue(result["recommended"])

    def test_custom_download_speed_affects_cost(self) -> None:
        # Slower download (0.1 GB/s) increases download time and cost, can make cache worthwhile.
        result = weight_cache.cost_check(
            weight_gb=100,
            hourly_usd=2.0,
            starts_per_month=30,
            download_gbps=0.1,
        )
        # 100 / 0.1 = 1000 seconds per download; 30 downloads = 30000 seconds = 30000/3600 hours
        # cost = 30000/3600 * 2.0 = $16.67
        self.assertAlmostEqual(result["download_usd_month"], 30000 / 3600 * 2.0, places=2)
        self.assertTrue(result["recommended"])

    def test_headroom_affects_volume_size(self) -> None:
        result = weight_cache.cost_check(
            weight_gb=100,
            hourly_usd=1.0,
            starts_per_month=1,
            headroom=1.5,
        )
        self.assertEqual(result["volume_gb"], 150)  # ceil(100 * 1.5)
        # storage cost increases with headroom.
        self.assertAlmostEqual(result["storage_usd_month"], 150 * 0.07, places=2)

    def test_volume_fields_default_mount(self) -> None:
        result = weight_cache.volume_fields("vol-123456")
        self.assertEqual(result["body"]["networkVolumeId"], "vol-123456")
        self.assertEqual(result["body"]["volumeMountPath"], "/runpod-volume")
        self.assertEqual(result["env"]["HF_HOME"], "/runpod-volume/hf")

    def test_volume_fields_custom_mount(self) -> None:
        result = weight_cache.volume_fields("vol-custom", mount="/mnt/custom")
        self.assertEqual(result["body"]["networkVolumeId"], "vol-custom")
        self.assertEqual(result["body"]["volumeMountPath"], "/mnt/custom")
        self.assertEqual(result["env"]["HF_HOME"], "/mnt/custom/hf")

    def test_volume_fields_shape(self) -> None:
        result = weight_cache.volume_fields("vol-abc")
        self.assertIn("body", result)
        self.assertIn("env", result)
        self.assertIsInstance(result["body"], dict)
        self.assertIsInstance(result["env"], dict)
        self.assertIn("networkVolumeId", result["body"])
        self.assertIn("volumeMountPath", result["body"])
        self.assertIn("HF_HOME", result["env"])


if __name__ == "__main__":
    unittest.main()
