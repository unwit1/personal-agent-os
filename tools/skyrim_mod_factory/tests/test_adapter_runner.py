import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("run_adapter",ROOT/"run_adapter.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class AdapterRunnerTests(unittest.TestCase):
    def test_substitution(self):
        self.assertEqual(MOD.subst("{root}/Tool.exe",{"root":"C:/X"}),"C:/X/Tool.exe")

    def test_missing_substitution(self):
        with self.assertRaises(ValueError):
            MOD.subst("{root}/{missing}",{"root":"X"})

    def test_file_fact_missing(self):
        fact=MOD.file_fact("__definitely_missing_skyrim_factory_test__")
        self.assertFalse(fact["exists"])

    def test_build_invocation(self):
        adapter={
            "adapter_id":"fixture",
            "invocation":{
                "mode":"cli",
                "executable":"{tool}",
                "arguments_template":["--input","{input}"],
                "working_directory":"{cwd}",
                "environment":{"FIXTURE_VALUE":"{value}"},
            }
        }
        inv=MOD.build_invocation(adapter,{
            "tool":"tool.exe",
            "input":"input.txt",
            "cwd":"C:/work",
            "value":"ok",
        })
        self.assertEqual(inv["argv"],["tool.exe","--input","input.txt"])
        self.assertEqual(inv["cwd"],"C:/work")
        self.assertEqual(inv["env"]["FIXTURE_VALUE"],"ok")

    def test_run_adapter_dry_run_is_safe_and_records_evidence(self):
        adapter={
            "adapter_id":"fixture",
            "tool":"Fixture Tool",
            "tool_version":"1.0",
            "invocation":{
                "mode":"cli",
                "executable":"python",
                "arguments_template":["-c","print('should not execute')"],
            },
            "evidence":{"source_url":"https://example.invalid/fixture"},
        }
        with tempfile.TemporaryDirectory() as td:
            record=MOD.run_adapter(
                adapter,
                adapter_id="fixture",
                log_dir=Path(td),
                execute=False,
                record_id="step.fixture",
            )
        self.assertEqual(record["id"],"step.fixture")
        self.assertEqual(record["adapter_id"],"fixture")
        self.assertEqual(record["status"],"skipped")
        self.assertTrue(record["dry_run"])
        self.assertIsNone(record["exit_code"])
        self.assertIn("dry-run",record["issues"][0])

    def test_run_adapter_rejects_non_cli_adapter(self):
        adapter={"adapter_id":"library-only","invocation":{"mode":"library"}}
        with self.assertRaises(ValueError):
            MOD.run_adapter(adapter,adapter_id="library-only",execute=False)

    def test_forbidden_log_pattern_fails_zero_exit_code(self):
        adapter={"success":{"exit_codes":[0],"forbidden_log_patterns":["FATAL"]}}
        verdict=MOD.evaluate_process_result(
            adapter,returncode=0,stdout="FATAL: bad graph",stderr="",outputs_after=[]
        )
        self.assertEqual(verdict["status"],"failed")
        self.assertIn("FORBIDDEN_LOG_PATTERN",verdict["issue_codes"])

    def test_warning_diagnostic_is_evidence_but_not_failure(self):
        adapter={"diagnostics":[{
            "issue_code":"CACHE_STALE",
            "pattern":"stale cache",
            "stream":"stderr",
            "severity":"WARNING",
            "analyzer_rule_id":"SKYRIM-GENERATED-OUTPUT-STALE",
        }]}
        verdict=MOD.evaluate_process_result(
            adapter,returncode=0,stdout="",stderr="stale cache detected",outputs_after=[]
        )
        self.assertEqual(verdict["status"],"passed")
        self.assertIn("CACHE_STALE",verdict["issue_codes"])
        self.assertIn("SKYRIM-GENERATED-OUTPUT-STALE",verdict["analyzer_rule_ids"])

    def test_error_diagnostic_fails_and_emits_rule_id(self):
        adapter={"diagnostics":[{
            "issue_code":"STALE_OUTPUT",
            "pattern":"output is stale",
            "severity":"ERROR",
            "analyzer_rule_id":"SKYRIM-GENERATED-OUTPUT-STALE",
        }]}
        verdict=MOD.evaluate_process_result(
            adapter,returncode=0,stdout="output is stale",stderr="",outputs_after=[]
        )
        self.assertEqual(verdict["status"],"failed")
        self.assertIn("SKYRIM-GENERATED-OUTPUT-STALE",verdict["analyzer_rule_ids"])

    def test_missing_declared_output_fails(self):
        verdict=MOD.evaluate_process_result(
            {"success":{"exit_codes":[0]}},
            returncode=0,
            stdout="ok",
            stderr="",
            outputs_after=[{"path":"missing.txt","exists":False}],
        )
        self.assertEqual(verdict["status"],"failed")
        self.assertIn("DECLARED_OUTPUT_MISSING",verdict["issue_codes"])

if __name__=="__main__":
    unittest.main()
