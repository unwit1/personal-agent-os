"""MIE-0017: OTLP/JSON trace projection of orchestrated runs."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator import trace  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402

from test_orchestrator import OrchestratorFixture  # noqa: E402

GOAL_MARKER = "SECRET-GOAL-7f3a"
SUMMARY_MARKER = "SECRET-SUMMARY-91bc"


class TraceProjectionTests(OrchestratorFixture):
    def run_with(self, script) -> tuple[str, dict]:
        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("a", goal=f"do the thing {GOAL_MARKER}")], max_stage_retries=0, max_escalations=0, provider_failover=False)
        self.engine.run_loop(run_id, max_ticks=40)
        document = trace.export(run_id, home=self.tmp / "home")["document"]
        return run_id, document

    def spans(self, document: dict) -> list[dict]:
        return document["resourceSpans"][0]["scopeSpans"][0]["spans"]

    @staticmethod
    def attrs(span: dict) -> dict:
        return {item["key"]: next(iter(item["value"].values())) for item in span["attributes"]}

    def test_structure_and_genai_attributes(self) -> None:
        def script(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            return {"edits": {"a/x.txt": "x\n"}, "structured": {"status": "done", "summary": SUMMARY_MARKER}, "usage": {"input_tokens": 120, "output_tokens": 30}}

        run_id, document = self.run_with(script)
        spans = self.spans(document)
        ids = {span["spanId"] for span in spans}
        self.assertEqual(len({span["traceId"] for span in spans}), 1)
        roots = [span for span in spans if "parentSpanId" not in span]
        self.assertEqual(len(roots), 1)
        self.assertEqual(self.attrs(roots[0])["gen_ai.operation.name"], "invoke_workflow")
        self.assertTrue(all(span["parentSpanId"] in ids for span in spans if "parentSpanId" in span))
        agents = [span for span in spans if self.attrs(span).get("gen_ai.operation.name") == "invoke_agent"]
        self.assertGreaterEqual(len(agents), 2)  # implementer + reviewer
        implementer = next(span for span in agents if self.attrs(span).get("gen_ai.agent.name") == "implementer")
        attrs = self.attrs(implementer)
        self.assertEqual((attrs["gen_ai.provider.name"], attrs["gen_ai.usage.input_tokens"], attrs["gen_ai.usage.output_tokens"]), ("alpha", "120", "30"))
        self.assertIn("gen_ai.response.model", attrs)
        self.assertTrue(any(self.attrs(span).get("gen_ai.operation.name") == "execute_tool" for span in spans))
        for span in spans:
            self.assertLessEqual(int(span["startTimeUnixNano"]), int(span["endTimeUnixNano"]))

    def test_failure_is_marked_and_no_content_is_exported(self) -> None:
        def script(request, call):
            return {"failure": "failed", "detail": f"crash with {SUMMARY_MARKER}"}

        _, document = self.run_with(script)
        text = json.dumps(document)
        self.assertNotIn(GOAL_MARKER, text)
        self.assertNotIn(SUMMARY_MARKER, text)
        failed = [span for span in self.spans(document) if span["status"]["code"] == 2]
        self.assertTrue(failed)
        self.assertTrue(any(self.attrs(span).get("error.type") == "failed" for span in failed))

    def test_missing_run_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileNotFoundError):
            trace.export("run-missing", home=Path(tmp))
