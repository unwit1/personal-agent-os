from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agent_os import cli
from agent_os.executive.window import server


class CommandCenterAppTests(unittest.TestCase):
    def test_cli_flags_dispatch_without_starting_real_server(self):
        with patch.object(server, "serve_app", return_value=0) as serve:
            self.assertEqual(cli.main(["app", "--no-window", "--port", "9999", "--remote-host", "pc.test", "--remote-host", "pc.test:443"]), 0)
        serve.assert_called_once_with(port=9999, open_window=False, remote_hosts=("pc.test", "pc.test:443"))

    def test_app_starts_both_servers_opens_window_and_closes(self):
        closed = threading.Event()
        control = SimpleNamespace(server_address=("127.0.0.1", 4567), api=SimpleNamespace(start_model_checks=Mock()),
                                  serve_forever=lambda: closed.wait(3), shutdown=Mock(side_effect=closed.set), server_close=Mock())
        wake = SimpleNamespace(monitor=Mock())
        executive = SimpleNamespace(server_address=("127.0.0.1", 9876), api=SimpleNamespace(wake=wake),
                                    serve_forever=Mock(side_effect=KeyboardInterrupt), server_close=Mock())
        control_builder = Mock(return_value=(control, "token"))
        executive_builder = Mock(return_value=(executive, "token"))
        opener = Mock()
        with patch("agent_os.orchestrator.foreman_deploy.manager") as manager, patch("builtins.print"):
            self.assertEqual(server.serve_app(port=9876, remote_hosts=("pc.test",), orchestrator_builder=control_builder,
                             executive_builder=executive_builder, opener=opener, active=lambda: False), 0)
        control_builder.assert_called_once_with(host="127.0.0.1", port=0)
        self.assertEqual(executive_builder.call_args.kwargs["orchestrator_url"], "http://127.0.0.1:4567/")
        self.assertEqual(executive_builder.call_args.kwargs["remote_hosts"], ("pc.test",))
        opener.assert_called_once_with("http://127.0.0.1:9876/")
        control.api.start_model_checks.assert_called_once()
        manager.return_value.resume.assert_called_once()
        control.shutdown.assert_called_once()
        control.server_close.assert_called_once()
        executive.server_close.assert_called_once()
        wake.monitor.assert_called_once()

    def test_no_window_and_startup_failure_clean_up(self):
        control = SimpleNamespace(server_address=("127.0.0.1", 1), api=SimpleNamespace(start_model_checks=Mock()),
                                  serve_forever=Mock(), shutdown=Mock(), server_close=Mock())
        executive = SimpleNamespace(server_address=("127.0.0.1", 2), api=SimpleNamespace(wake=SimpleNamespace(monitor=Mock())),
                                    serve_forever=Mock(), server_close=Mock())
        opener = Mock()
        with patch("agent_os.orchestrator.foreman_deploy.manager"), patch("builtins.print"):
            server.serve_app(open_window=False, orchestrator_builder=lambda **_: (control, "token"),
                             executive_builder=lambda **_: (executive, "token"), opener=opener)
        opener.assert_not_called()
        broken = Mock(side_effect=ValueError("failed"))
        with self.assertRaises(ValueError):
            server.serve_app(orchestrator_builder=lambda **_: (control, "token"), executive_builder=broken)
        self.assertEqual(control.server_close.call_count, 2)

    def test_active_runs_probe(self):
        with patch("agent_os.orchestrator.service.list_runs", return_value=[{"state": "PAUSED"}, {"state": "COMPLETE"}]):
            self.assertFalse(server._runs_active())
        with patch("agent_os.orchestrator.service.list_runs", return_value=[{"state": "RUNNING"}]):
            self.assertTrue(server._runs_active())

    def test_tabs_and_ui_wiring_preserve_preview_confirm(self):
        html = (ROOT / "gui" / "executive.html").read_text(encoding="utf-8")
        js = (ROOT / "gui" / "executive.js").read_text(encoding="utf-8")
        for tab in ("today", "projects", "runs", "chat", "usage"):
            self.assertIn(f'id="cc-tab-{tab}"', html)
            self.assertIn(f'aria-controls="cc-{tab}"', html)
        for endpoint in ("/api/usage", "/api/extras", "/api/open-url", "/api/chat/providers", "/api/chat/conversations",
                         "/api/chat/conversation?id=", "/api/chat/send", "/api/chat/delete", "/api/projects",
                         "/api/projects/resume", "/api/cloud/preview", "/api/config"):
            self.assertIn(endpoint, js)
        self.assertIn('title="Orchestrator runs and model services"', html)
        self.assertIn("option.disabled = Boolean(project && project.sensitive && !provider.sensitive_ok)", js)
        self.assertIn("textContent", js)
        self.assertNotIn("innerHTML", js.split("const hub =", 1)[1])
        self.assertEqual(js.count("'/api/confirm'"), 1)
        self.assertIn("prefers-color-scheme: dark", (ROOT / "gui" / "style.css").read_text())


if __name__ == "__main__":
    unittest.main()
