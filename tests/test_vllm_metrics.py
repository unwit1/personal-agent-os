"""Tests for vLLM metrics parsing and rate calculations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from agent_os.orchestrator import vllm_metrics


class TestParseMetrics(unittest.TestCase):
    """Test vLLM Prometheus metrics parsing."""

    METRICS_TEXT = """\
# HELP vllm:num_requests_running Number of requests currently running
# TYPE vllm:num_requests_running gauge
vllm:num_requests_running 4

# HELP vllm:num_requests_waiting Number of requests waiting for processing
# TYPE vllm:num_requests_waiting gauge
vllm:num_requests_waiting 2

# HELP vllm:prompt_tokens_total Total number of prompt tokens processed
# TYPE vllm:prompt_tokens_total counter
vllm:prompt_tokens_total 50000

# HELP vllm:generation_tokens_total Total number of generation tokens produced
# TYPE vllm:generation_tokens_total counter
vllm:generation_tokens_total 25000

# HELP vllm:request_success_total Total number of successful requests
# TYPE vllm:request_success_total counter
vllm:request_success_total 100

# HELP vllm:gpu_cache_usage_perc GPU KV cache usage percentage
# TYPE vllm:gpu_cache_usage_perc gauge
vllm:gpu_cache_usage_perc{gpu_id="0"} 45.0
vllm:gpu_cache_usage_perc{gpu_id="1"} 60.0

# HELP vllm:kv_cache_usage_perc KV cache usage percentage
# TYPE vllm:kv_cache_usage_perc gauge
vllm:kv_cache_usage_perc{layer="0"} 30.0
vllm:kv_cache_usage_perc{layer="1"} 35.0

# HELP vllm:gpu_prefix_cache_hits_total GPU prefix cache hits
# TYPE vllm:gpu_prefix_cache_hits_total counter
vllm:gpu_prefix_cache_hits_total 1500

# HELP vllm:prefix_cache_hits_total Prefix cache hits
# TYPE vllm:prefix_cache_hits_total counter
vllm:prefix_cache_hits_total 500

# HELP vllm:gpu_prefix_cache_queries_total GPU prefix cache queries
# TYPE vllm:gpu_prefix_cache_queries_total counter
vllm:gpu_prefix_cache_queries_total 2000

# HELP vllm:prefix_cache_queries_total Prefix cache queries
# TYPE vllm:prefix_cache_queries_total counter
vllm:prefix_cache_queries_total 1000
"""

    def test_parse_basic_metrics(self):
        """Test parsing basic counter metrics."""
        result = vllm_metrics.parse(self.METRICS_TEXT)
        self.assertEqual(result["running"], 4.0)
        self.assertEqual(result["waiting"], 2.0)
        self.assertEqual(result["prompt_tokens"], 50000.0)
        self.assertEqual(result["generation_tokens"], 25000.0)
        self.assertEqual(result["requests"], 100.0)

    def test_parse_kv_usage_max_across_labels(self):
        """Test that kv_usage takes max across labels."""
        result = vllm_metrics.parse(self.METRICS_TEXT)
        # gpu_cache_usage_perc: max(45.0, 60.0) = 60.0
        # kv_cache_usage_perc: max(30.0, 35.0) = 35.0
        # Final kv_usage should be max of all: 60.0
        self.assertEqual(result["kv_usage"], 60.0)

    def test_parse_prefix_cache_metrics_sum_across_labels(self):
        """Test that prefix_hits and prefix_queries sum across sources."""
        result = vllm_metrics.parse(self.METRICS_TEXT)
        # prefix_hits: gpu=1500, regular=500 -> sum=2000
        # prefix_queries: gpu=2000, regular=1000 -> sum=3000
        self.assertEqual(result["prefix_hits"], 2000.0)
        self.assertEqual(result["prefix_queries"], 3000.0)

    def test_parse_empty_text(self):
        """Test parsing empty metrics text."""
        result = vllm_metrics.parse("")
        self.assertEqual(result, {})

    def test_parse_none_text(self):
        """Test parsing None metrics text."""
        result = vllm_metrics.parse(None)
        self.assertEqual(result, {})

    def test_parse_comments_and_whitespace(self):
        """Test that comments and empty lines are skipped."""
        text = """
# Comment line
vllm:num_requests_running 5

# Another comment
vllm:num_requests_waiting 1
"""
        result = vllm_metrics.parse(text)
        self.assertEqual(result["running"], 5.0)
        self.assertEqual(result["waiting"], 1.0)
        self.assertNotIn("comment", str(result).lower())

    def test_parse_malformed_lines(self):
        """Test that malformed lines are skipped silently."""
        text = """
vllm:num_requests_running 5
malformed_line_without_value
vllm:num_requests_waiting not_a_number
vllm:prompt_tokens_total 1000
vllm:prompt_tokens_total 1000 extra garbage at end
"""
        result = vllm_metrics.parse(text)
        self.assertEqual(result["running"], 5.0)
        self.assertEqual(result["prompt_tokens"], 1000.0)
        self.assertNotIn("waiting", result)

    def test_parse_unknown_metrics_ignored(self):
        """Test that unknown metrics are ignored."""
        text = """
vllm:num_requests_running 5
vllm:unknown_metric 999
vllm:num_requests_waiting 1
"""
        result = vllm_metrics.parse(text)
        self.assertEqual(result["running"], 5.0)
        self.assertEqual(result["waiting"], 1.0)
        self.assertEqual(len(result), 2)

    def test_parse_summing_labeled_counters(self):
        """Test that labeled counters are summed."""
        text = """
vllm:request_success_total{model="a"} 50
vllm:request_success_total{model="b"} 30
"""
        result = vllm_metrics.parse(text)
        self.assertEqual(result["requests"], 80.0)


class TestPrefixHitRate(unittest.TestCase):
    """Test prefix cache hit rate calculation."""

    def test_hit_rate_basic(self):
        """Test basic hit rate calculation."""
        prev = {"prefix_hits": 100.0, "prefix_queries": 200.0}
        cur = {"prefix_hits": 150.0, "prefix_queries": 300.0}
        # New hits: 150-100=50, New queries: 300-200=100
        # Rate: 50/100 = 0.5
        rate = vllm_metrics.prefix_hit_rate(prev, cur)
        self.assertAlmostEqual(rate, 0.5)

    def test_hit_rate_perfect_hits(self):
        """Test perfect hit rate."""
        prev = {"prefix_hits": 0.0, "prefix_queries": 0.0}
        cur = {"prefix_hits": 100.0, "prefix_queries": 100.0}
        rate = vllm_metrics.prefix_hit_rate(prev, cur)
        self.assertAlmostEqual(rate, 1.0)

    def test_hit_rate_no_hits(self):
        """Test zero hit rate."""
        prev = {"prefix_hits": 100.0, "prefix_queries": 100.0}
        cur = {"prefix_hits": 100.0, "prefix_queries": 200.0}
        # New hits: 0, New queries: 100 -> rate = 0.0
        rate = vllm_metrics.prefix_hit_rate(prev, cur)
        self.assertAlmostEqual(rate, 0.0)

    def test_hit_rate_no_new_queries(self):
        """Test that None is returned when there are no new queries."""
        prev = {"prefix_hits": 100.0, "prefix_queries": 200.0}
        cur = {"prefix_hits": 150.0, "prefix_queries": 200.0}
        # No new queries
        rate = vllm_metrics.prefix_hit_rate(prev, cur)
        self.assertIsNone(rate)

    def test_hit_rate_prev_none(self):
        """Test that None is returned when prev is None."""
        cur = {"prefix_hits": 100.0, "prefix_queries": 200.0}
        rate = vllm_metrics.prefix_hit_rate(None, cur)
        self.assertIsNone(rate)

    def test_hit_rate_cur_none(self):
        """Test that None is returned when cur is None."""
        prev = {"prefix_hits": 100.0, "prefix_queries": 200.0}
        rate = vllm_metrics.prefix_hit_rate(prev, None)
        self.assertIsNone(rate)

    def test_hit_rate_missing_keys(self):
        """Test hit rate with missing keys (defaults to 0)."""
        prev = {"prefix_hits": 100.0}  # missing prefix_queries
        cur = {"prefix_hits": 150.0, "prefix_queries": 300.0}
        # prev defaults: queries=0, cur queries=300
        # new queries: 300-0=300, new hits: 150-100=50
        # rate: 50/300 ≈ 0.167
        rate = vllm_metrics.prefix_hit_rate(prev, cur)
        self.assertAlmostEqual(rate, 50.0 / 300.0)


class TestTokensPerSecond(unittest.TestCase):
    """Test tokens per second calculation."""

    def test_tokens_per_second_basic(self):
        """Test basic tokens per second calculation."""
        prev = {"generation_tokens": 1000.0}
        cur = {"generation_tokens": 2000.0}
        # New tokens: 2000-1000=1000, Time: 10s
        # Rate: 1000/10 = 100 tok/s
        rate = vllm_metrics.tokens_per_second(prev, cur, 10.0)
        self.assertAlmostEqual(rate, 100.0)

    def test_tokens_per_second_fractional(self):
        """Test tokens per second with fractional seconds."""
        prev = {"generation_tokens": 1000.0}
        cur = {"generation_tokens": 1500.0}
        # New tokens: 500, Time: 2.5s -> 200 tok/s
        rate = vllm_metrics.tokens_per_second(prev, cur, 2.5)
        self.assertAlmostEqual(rate, 200.0)

    def test_tokens_per_second_no_progress(self):
        """Test that None is returned when there is no token progress."""
        prev = {"generation_tokens": 1000.0}
        cur = {"generation_tokens": 1000.0}
        rate = vllm_metrics.tokens_per_second(prev, cur, 10.0)
        self.assertIsNone(rate)

    def test_tokens_per_second_backward_progress(self):
        """Test that None is returned when tokens go backward."""
        prev = {"generation_tokens": 2000.0}
        cur = {"generation_tokens": 1000.0}
        rate = vllm_metrics.tokens_per_second(prev, cur, 10.0)
        self.assertIsNone(rate)

    def test_tokens_per_second_prev_none(self):
        """Test that None is returned when prev is None."""
        cur = {"generation_tokens": 1000.0}
        rate = vllm_metrics.tokens_per_second(None, cur, 10.0)
        self.assertIsNone(rate)

    def test_tokens_per_second_cur_none(self):
        """Test that None is returned when cur is None."""
        prev = {"generation_tokens": 1000.0}
        rate = vllm_metrics.tokens_per_second(prev, None, 10.0)
        self.assertIsNone(rate)

    def test_tokens_per_second_zero_seconds(self):
        """Test that None is returned with zero seconds."""
        prev = {"generation_tokens": 1000.0}
        cur = {"generation_tokens": 2000.0}
        rate = vllm_metrics.tokens_per_second(prev, cur, 0.0)
        self.assertIsNone(rate)

    def test_tokens_per_second_negative_seconds(self):
        """Test that None is returned with negative seconds."""
        prev = {"generation_tokens": 1000.0}
        cur = {"generation_tokens": 2000.0}
        rate = vllm_metrics.tokens_per_second(prev, cur, -5.0)
        self.assertIsNone(rate)

    def test_tokens_per_second_missing_key(self):
        """Test tokens per second with missing generation_tokens key."""
        prev = {"other_key": 1000.0}  # missing generation_tokens
        cur = {"generation_tokens": 1000.0}
        # prev defaults: generation_tokens=0, cur=1000
        # new tokens: 1000, time: 10s -> 100 tok/s
        rate = vllm_metrics.tokens_per_second(prev, cur, 10.0)
        self.assertAlmostEqual(rate, 100.0)


class TestMetricsConstant(unittest.TestCase):
    """Test the METRICS constant."""

    def test_metrics_superset(self):
        """Test that METRICS is a superset of foreman_deploy METRICS."""
        # Original foreman_deploy metrics
        expected_keys = {
            "vllm:num_requests_running",
            "vllm:num_requests_waiting",
            "vllm:prompt_tokens_total",
            "vllm:generation_tokens_total",
            "vllm:request_success_total",
        }
        for key in expected_keys:
            self.assertIn(key, vllm_metrics.METRICS)

    def test_metrics_new_keys(self):
        """Test that new KV-cache and prefix-cache metrics are present."""
        new_keys = {
            "vllm:gpu_cache_usage_perc",
            "vllm:kv_cache_usage_perc",
            "vllm:gpu_prefix_cache_hits_total",
            "vllm:prefix_cache_hits_total",
            "vllm:gpu_prefix_cache_queries_total",
            "vllm:prefix_cache_queries_total",
        }
        for key in new_keys:
            self.assertIn(key, vllm_metrics.METRICS)

    def test_gauge_keys_contains_kv_usage(self):
        """Test that kv_usage is in GAUGE_KEYS."""
        self.assertIn("kv_usage", vllm_metrics.GAUGE_KEYS)


class TestIntegration(unittest.TestCase):
    """Integration tests with realistic scenarios."""

    def test_full_metrics_parsing_and_calculation(self):
        """Test parsing metrics and calculating rates."""
        # Sample 1
        sample1_text = """\
vllm:num_requests_running 2
vllm:num_requests_waiting 1
vllm:prompt_tokens_total 10000
vllm:generation_tokens_total 5000
vllm:request_success_total 50
vllm:gpu_cache_usage_perc{gpu_id="0"} 40.0
vllm:gpu_prefix_cache_hits_total 1000
vllm:gpu_prefix_cache_queries_total 2000
"""
        sample1 = vllm_metrics.parse(sample1_text)

        # Sample 2 (10 seconds later)
        sample2_text = """\
vllm:num_requests_running 3
vllm:num_requests_waiting 2
vllm:prompt_tokens_total 15000
vllm:generation_tokens_total 7000
vllm:request_success_total 65
vllm:gpu_cache_usage_perc{gpu_id="0"} 55.0
vllm:gpu_prefix_cache_hits_total 1200
vllm:gpu_prefix_cache_queries_total 2500
"""
        sample2 = vllm_metrics.parse(sample2_text)

        # Verify parsing
        self.assertEqual(sample1["generation_tokens"], 5000.0)
        self.assertEqual(sample2["generation_tokens"], 7000.0)
        self.assertEqual(sample1["kv_usage"], 40.0)
        self.assertEqual(sample2["kv_usage"], 55.0)

        # Calculate rates
        tps = vllm_metrics.tokens_per_second(sample1, sample2, 10.0)
        self.assertAlmostEqual(tps, 200.0)  # (7000-5000)/10

        hit_rate = vllm_metrics.prefix_hit_rate(sample1, sample2)
        # New hits: 1200-1000=200, new queries: 2500-2000=500
        # Rate: 200/500 = 0.4
        self.assertAlmostEqual(hit_rate, 0.4)

    def test_old_metric_names_still_work(self):
        """Test backward compatibility with old metric names."""
        text = """\
vllm:num_requests_running 5
vllm:num_requests_waiting 1
vllm:prompt_tokens_total 1000
vllm:generation_tokens_total 500
vllm:request_success_total 10
"""
        result = vllm_metrics.parse(text)
        self.assertEqual(result["running"], 5.0)
        self.assertEqual(result["waiting"], 1.0)
        self.assertEqual(result["prompt_tokens"], 1000.0)
        self.assertEqual(result["generation_tokens"], 500.0)
        self.assertEqual(result["requests"], 10.0)


if __name__ == "__main__":
    unittest.main()
