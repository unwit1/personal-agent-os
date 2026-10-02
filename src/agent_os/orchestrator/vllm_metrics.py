"""Parse vLLM Prometheus metrics for throughput and utilization tracking.

Extends the basic metrics in foreman_deploy.METRICS with KV-cache usage,
prefix-cache hit rates, and token throughput for rented GPU utilization
monitoring (IMP-0015).
"""

METRICS = {
    "vllm:num_requests_running": "running",
    "vllm:num_requests_waiting": "waiting",
    "vllm:prompt_tokens_total": "prompt_tokens",
    "vllm:generation_tokens_total": "generation_tokens",
    "vllm:request_success_total": "requests",
    "vllm:gpu_cache_usage_perc": "kv_usage",
    "vllm:kv_cache_usage_perc": "kv_usage",
    "vllm:gpu_prefix_cache_hits_total": "prefix_hits",
    "vllm:prefix_cache_hits_total": "prefix_hits",
    "vllm:gpu_prefix_cache_queries_total": "prefix_queries",
    "vllm:prefix_cache_queries_total": "prefix_queries",
}

# Gauge metrics take the max across labels instead of sum
GAUGE_KEYS = {"kv_usage"}


def parse(text: str) -> dict[str, float]:
    """Parse vLLM Prometheus /metrics output.

    - Skips comments and empty lines
    - Ignores labels for key matching but uses them to track per-label values
    - For gauge keys (kv_usage), takes max across labels
    - For counter keys, sums across labels
    - Skips malformed lines silently
    """
    out: dict[str, float] = {}

    for line in (text or "").splitlines():
        if not line or line.startswith("#"):
            continue

        # Extract metric name before labels or space
        name = line.split("{", 1)[0].split(" ", 1)[0]
        key = METRICS.get(name)

        if not key:
            continue

        try:
            value = float(line.rsplit(" ", 1)[1])
        except (IndexError, ValueError):
            continue

        if key in GAUGE_KEYS:
            out[key] = max(out.get(key, value), value)
        else:
            out[key] = out.get(key, 0.0) + value

    return out


def prefix_hit_rate(prev: dict[str, float] | None, cur: dict[str, float]) -> float | None:
    """Calculate prefix cache hit rate between two samples.

    Args:
        prev: Previous cumulative sample (or None for first sample)
        cur: Current cumulative sample

    Returns:
        Hit rate (0.0-1.0) or None if there are no new queries
    """
    if not prev or not cur:
        return None

    prev_hits = prev.get("prefix_hits", 0.0)
    prev_queries = prev.get("prefix_queries", 0.0)
    cur_hits = cur.get("prefix_hits", 0.0)
    cur_queries = cur.get("prefix_queries", 0.0)

    new_queries = cur_queries - prev_queries
    if new_queries <= 0:
        return None

    new_hits = cur_hits - prev_hits
    return new_hits / new_queries


def tokens_per_second(
    prev: dict[str, float] | None, cur: dict[str, float], seconds: float
) -> float | None:
    """Calculate generation tokens per second between two samples.

    Args:
        prev: Previous cumulative sample (or None for first sample)
        cur: Current cumulative sample
        seconds: Time elapsed between samples

    Returns:
        Tokens per second or None if no progress or invalid time
    """
    if not cur or seconds <= 0:
        return None

    if not prev:
        return None

    prev_tokens = prev.get("generation_tokens", 0.0)
    cur_tokens = cur.get("generation_tokens", 0.0)

    new_tokens = cur_tokens - prev_tokens
    if new_tokens <= 0:
        return None

    return new_tokens / seconds
