import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
SPEC=importlib.util.spec_from_file_location("run_presentmon_capture",ROOT/"run_presentmon_capture.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class PresentMonCaptureTests(unittest.TestCase):
    def test_command_is_process_scoped_and_uses_current_cli_switches(self):
        cmd=MOD.build_command(
            Path("PresentMon.exe"),
            process_id=4242,
            output_csv=Path("trace.csv"),
            timed_seconds=15,
        )
        self.assertEqual(cmd[:5],[
            "PresentMon.exe","--process_id","4242","--output_file","trace.csv"
        ])
        self.assertIn("--v2_metrics",cmd)
        self.assertIn("--terminate_on_proc_exit",cmd)
        self.assertIn("--timed",cmd)
        self.assertIn("--terminate_after_timed",cmd)

    def test_summary_filters_target_pid_and_computes_nearest_rank_percentiles(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"trace.csv"
            path.write_text(
                "Application,ProcessID,FrameTime,CPUBusy,GPUTime\n"
                "SkyrimSE.exe,4242,10,5,4\n"
                "Other.exe,99,999,999,999\n"
                "SkyrimSE.exe,4242,20,8,7\n"
                "SkyrimSE.exe,4242,30,9,8\n",
                encoding="utf-8",
            )
            result=MOD.summarize_csv(path,4242)
        self.assertEqual(result["status"],"pass")
        self.assertEqual(result["frame_count"],3)
        self.assertEqual(result["metrics"]["FrameTime"]["mean"],20)
        self.assertEqual(result["metrics"]["FrameTime"]["p95"],30)
        self.assertEqual(result["metrics"]["GPUTime"]["max"],8)

    def test_missing_target_frames_fail(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"trace.csv"
            path.write_text(
                "Application,ProcessID,FrameTime\nOther.exe,99,10\n",
                encoding="utf-8",
            )
            result=MOD.summarize_csv(path,4242)
        self.assertEqual(result["status"],"fail")
        self.assertEqual(result["frame_count"],0)

    def test_missing_frame_time_metric_needs_review(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"trace.csv"
            path.write_text(
                "Application,ProcessID,GPUBusy\nSkyrimSE.exe,4242,3\n",
                encoding="utf-8",
            )
            result=MOD.summarize_csv(path,4242)
        self.assertEqual(result["status"],"needs-review")

    def test_missing_process_id_column_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"trace.csv"
            path.write_text("Application,FrameTime\nSkyrimSE.exe,10\n",encoding="utf-8")
            result=MOD.summarize_csv(path,4242)
        self.assertEqual(result["status"],"fail")
        self.assertIn("missing ProcessID",result["issues"][0])

    def test_summary_conforms_to_typed_schema(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"trace.csv"
            path.write_text(
                "Application,ProcessID,FrameTime\nSkyrimSE.exe,4242,10\n",
                encoding="utf-8",
            )
            result=MOD.summarize_csv(path,4242)
        schema=json.loads(
            (REPO/"schemas"/"skyrim-frame-trace-summary-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(result)),[])

if __name__=="__main__":
    unittest.main()
