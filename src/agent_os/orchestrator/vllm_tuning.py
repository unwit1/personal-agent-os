"""vLLM throughput tuning: adaptive concurrency, prefix caching, KV cache dtype and sizing."""

from __future__ import annotations

from .foreman_deploy import MAX_CONTEXT

FP8_KV_GPU_MARKERS = ("H100", "H200", "H20", "L4", "L40", "RTX 4090", "RTX 6000 Ada", "B200", "RTX 5090")


def fp8_kv_supported(gpu_id: str) -> bool:
    """Check if a GPU supports fp8 KV cache (case-insensitive, flexible spacing)."""
    if not gpu_id:
        return False
    # Normalize: lowercase, replace dashes/underscores with spaces, collapse spaces
    def normalize(s: str) -> str:
        return " ".join(s.lower().replace("-", " ").replace("_", " ").split())

    gpu_id_norm = normalize(gpu_id)
    return any(normalize(marker) in gpu_id_norm for marker in FP8_KV_GPU_MARKERS)


def max_num_seqs(
    model: dict,
    gpu_count: int,
    vram_gb_per_gpu: float,
    *,
    gpu_memory_utilization: float = 0.90,
    kv_dtype_bytes: int = 2,
    context: int | None = None,
    floor: int = 4,
    ceiling: int = 256,
) -> int:
    """Compute max concurrent sequences based on available KV cache.

    free_kv_bytes = gpu_count * vram_gb * 1e9 * util - weight_gb * 1e9 * 1.1
    per_seq = kv_bytes_per_token_scaled * avg_tokens
    avg_tokens = context // 4 (sequences rarely fill the window)
    Result clamped to [floor, ceiling], return floor if missing or no headroom.
    """
    kv_bytes_per_token = model.get("kv_bytes_per_token")
    weight_gb = model.get("weight_gb")

    if not kv_bytes_per_token or not weight_gb:
        return floor

    # Total VRAM available minus model weights (with overhead)
    total_vram_bytes = gpu_count * vram_gb_per_gpu * 1e9
    weight_overhead_bytes = weight_gb * 1e9 * 1.1
    free_kv_bytes = total_vram_bytes * gpu_memory_utilization - weight_overhead_bytes

    if free_kv_bytes <= 0:
        return floor

    # Scale KV dtype: model assumes 2-byte KV, scale by actual dtype
    kv_bytes_per_token_scaled = kv_bytes_per_token * (kv_dtype_bytes / 2)

    # Average tokens per sequence: sequences rarely fill the window
    avg_context = context or MAX_CONTEXT
    avg_tokens = avg_context // 4

    # Bytes per sequence for KV cache
    bytes_per_seq = kv_bytes_per_token_scaled * avg_tokens

    if bytes_per_seq <= 0:
        return floor

    # Number of concurrent sequences
    max_seqs = int(free_kv_bytes / bytes_per_seq)

    # Clamp to [floor, ceiling]
    return max(floor, min(max_seqs, ceiling))


def throughput_args(
    model: dict,
    choice: dict,
    overrides: dict | None = None,
) -> list[str]:
    """Generate vLLM throughput flags: prefix caching, chunked prefill, max_num_seqs, kv_cache_dtype.

    choice has: gpu_id, gpu_count, vram_gb
    overrides dict keys: prefix_caching, chunked_prefill, max_num_seqs, kv_cache_dtype
    - False/None removes that flag
    - Each override wins over computed value
    """
    overrides = overrides or {}
    args = []

    # --enable-prefix-caching
    prefix_caching = overrides.get("prefix_caching", True)
    if prefix_caching is not False:
        args.append("--enable-prefix-caching")

    # --enable-chunked-prefill
    chunked_prefill = overrides.get("chunked_prefill", True)
    if chunked_prefill is not False:
        args.append("--enable-chunked-prefill")

    # Resolve effective kv_cache_dtype (override takes precedence)
    gpu_id = choice.get("gpu_id", "")
    if "kv_cache_dtype" in overrides:
        effective_kv_dtype = overrides["kv_cache_dtype"]
    elif fp8_kv_supported(gpu_id):
        effective_kv_dtype = "fp8"
    else:
        effective_kv_dtype = None

    # --max-num-seqs N
    if "max_num_seqs" in overrides:
        max_seqs = overrides["max_num_seqs"]
        if max_seqs is not False and max_seqs is not None:
            args.extend(["--max-num-seqs", str(max_seqs)])
    else:
        # Compute automatically: use fp8 scaling only if effective dtype starts with 'fp8'
        kv_dtype_bytes = 1 if (effective_kv_dtype and effective_kv_dtype.startswith("fp8")) else 2
        max_seqs = max_num_seqs(
            model,
            choice.get("gpu_count", 1),
            choice.get("vram_gb", 0),
            kv_dtype_bytes=kv_dtype_bytes,
            context=model.get("context"),
        )
        args.extend(["--max-num-seqs", str(max_seqs)])

    # --kv-cache-dtype (only when not False/None)
    if effective_kv_dtype is not False and effective_kv_dtype is not None:
        args.extend(["--kv-cache-dtype", str(effective_kv_dtype)])

    return args
