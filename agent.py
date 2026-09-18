"""Dependency-free local launcher for Personal Agent OS development."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from agent_os.cli import main  # noqa: E402


raise SystemExit(main())
