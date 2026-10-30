"""Start the real Executive window with the real Shopping adapter on a fixed port (used by shopping_ui.e2e.js)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import tempfile
import time

from types import SimpleNamespace

from agent_os.executive.window.registry import Registry
from agent_os.executive.window.server import build_server

port = int(sys.argv[1])
home = Path(tempfile.mkdtemp(prefix="exec-window-"))
# Empty registry + inert chat bridge: this run exercises the Shopping tab only, so it does not need the Work/Personal providers
# (which import the Ingester Engine). The Shopping adapter is the real default one (env AGENT_SHOPPING_CMD / AGENT_SHOPPING_HOME).
server, _token = build_server("127.0.0.1", port, registry=Registry(), bridge=SimpleNamespace(send=lambda *a: {}), home=home)
print(f"READY {server.server_address[1]}", flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
