import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[3]
FACTORY=ROOT/"tools"/"skyrim_mod_factory"

SPEC=importlib.util.spec_from_file_location("run_adapter",FACTORY/"run_adapter.py")
RUN=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)

class BuildReportSchemaTests(unittest.TestCase):
    def test_adapter_dry_run_record_fits_build_report_step_schema(self):
        schema=json.loads(
            (ROOT/"schemas"/"skyrim-mod-build-report-v1.schema.json").read_text(encoding="utf-8")
        )
        adapter={
            "adapter_id":"fixture",
            "tool":"Fixture Tool",
            "tool_version":"1.0",
            "invocation":{
                "mode":"cli",
                "executable":"python",
                "arguments_template":["-c","print('not executed')"],
            },
            "evidence":{"source_url":"https://example.invalid/fixture"},
        }
        with tempfile.TemporaryDirectory() as td:
            step=RUN.run_adapter(
                adapter,
                adapter_id="fixture",
                log_dir=Path(td),
                execute=False,
                record_id="fixture.step",
            )
        report={
            "schema_version":"skyrim-mod-build-report-v1",
            "project_id":"fixture-project",
            "build_id":"fixture-build",
            "started_at":"2026-09-24T00:00:00+00:00",
            "status":"running",
            "steps":[step],
            "gates":[],
        }
        errors=list(Draft202012Validator(schema).iter_errors(report))
        self.assertEqual([],[(list(e.absolute_path),e.message) for e in errors])

if __name__=="__main__":
    unittest.main()
