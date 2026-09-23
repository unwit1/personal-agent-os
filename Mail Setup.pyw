"""Double-click to open the Agent OS mail account window (no console)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from agent_os.mail.setup_window import run  # noqa: E402

raise SystemExit(run())
