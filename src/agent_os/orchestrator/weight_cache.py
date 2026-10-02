"""Weight caching for rented GPUs: cost analysis and RunPod volume integration.

Rented models can optionally attach a RunPod network volume to cache model weights
across pod starts. This module compares the cost of storage (/month) against the
savings from avoiding re-downloading the weights on each pod restart, to determine
whether a volume is cost-effective for a given deployment.
"""

from __future__ import annotations

import math
from typing import Any

DEFAULT_VOLUME_USD_PER_GB_MONTH = 0.07
DEFAULT_DOWNLOAD_GBPS = 0.5


def cost_check(
    weight_gb: float,
    hourly_usd: float,
    starts_per_month: int,
    *,
    usd_per_gb_month: float = DEFAULT_VOLUME_USD_PER_GB_MONTH,
    download_gbps: float = DEFAULT_DOWNLOAD_GBPS,
    headroom: float = 1.2,
) -> dict[str, Any]:
    """Analyze the cost of a weight-caching volume vs. re-downloading on each restart.

    Args:
        weight_gb: Model weight size in GB.
        hourly_usd: Pod hourly cost in USD.
        starts_per_month: Expected pod restarts per month.
        usd_per_gb_month: Storage cost per GB per month (default: $0.07).
        download_gbps: Download speed in GB/s (default: 0.5 from Hugging Face hub).
        headroom: Storage headroom factor (default: 1.2 = 20% extra space).

    Returns:
        dict with:
        - volume_gb: Allocated volume size in GB.
        - storage_usd_month: Monthly storage cost in USD.
        - download_minutes_per_start: Minutes to download weights on each start.
        - download_usd_month: Monthly cost of download time across all starts.
        - saves_usd_month: Net monthly savings (negative if not recommended).
        - recommended: bool, True if saves_usd_month > 0.
    """
    volume_gb = math.ceil(weight_gb * headroom)
    storage_usd_month = volume_gb * usd_per_gb_month

    download_seconds_per_start = weight_gb / download_gbps
    download_minutes_per_start = download_seconds_per_start / 60

    download_usd_month = starts_per_month * download_seconds_per_start / 3600 * hourly_usd
    saves_usd_month = download_usd_month - storage_usd_month

    return {
        "volume_gb": volume_gb,
        "storage_usd_month": storage_usd_month,
        "download_minutes_per_start": download_minutes_per_start,
        "download_usd_month": download_usd_month,
        "saves_usd_month": saves_usd_month,
        "recommended": saves_usd_month > 0,
    }


def volume_fields(volume_id: str, mount: str = "/runpod-volume") -> dict[str, Any]:
    """RunPod pod-body fields for a network volume cache.

    Args:
        volume_id: RunPod network volume ID.
        mount: Mount path inside the pod (default: /runpod-volume).

    Returns:
        dict with 'body' and 'env' keys for merging into pod_request():
        - body: {'networkVolumeId': volume_id, 'volumeMountPath': mount}
        - env: {'HF_HOME': mount + '/hf'} to cache Hugging Face weights.
    """
    return {
        "body": {
            "networkVolumeId": volume_id,
            "volumeMountPath": mount,
        },
        "env": {
            "HF_HOME": f"{mount}/hf",
        },
    }
