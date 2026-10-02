"""Personal Agent OS core package."""

__version__ = "0.1.0"

from .ingester_bridge import ensure_ingester_engine as _ensure_ingester_engine  # noqa: E402

_ensure_ingester_engine()
