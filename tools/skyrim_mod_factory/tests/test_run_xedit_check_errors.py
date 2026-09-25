import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "run_xedit_check_errors",
    ROOT/"run_xedit_check_errors.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

CLEAN_LOG="""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [04] CleanPatch.esp
[00:00] Done: Checking for Errors, Processed Records: 10, Errors found: 0, Elapsed Time: 00:00
"""

BROKEN_LOG="""[00:00] Start: Checking for Errors
[00:00] Checking for Errors in [04] Broken.esp
[00:00] Example [ARMO:04000001]
[00:00] ARMO -> < Error: Could not be resolved >
[00:01] Done: Checking for Errors, Processed Records: 10, Errors found: 1, Elapsed Time: 00:01
"""

class RunXEditCheckErrorsTests(unittest.TestCase):
    def test_build_command_uses_documented_tool_mode_and_log_switch(self):
        cmd=MOD.build_command(
            Path("C:/Tools/SSEEdit.exe"),
            "Patch.esp",
            Path("C:/Runs/xedit.log"),
            game_mode="SSE",
            data_path=Path("C:/Games/Skyrim Special Edition/Data"),
            plugins_file=Path("C:/MO2/profiles/Test/plugins.txt"),
        )
        self.assertEqual(cmd[0],"C:/Tools/SSEEdit.exe")
        self.assertIn("-SSE",cmd)
        self.assertIn("-checkforerrors",cmd)
        self.assertIn("-quickedit:Patch.esp",cmd)
        self.assertIn("-autoload",cmd)
        self.assertIn("-autoexit",cmd)
        self.assertIn("-R:C:/Runs/xedit.log",cmd)
        self.assertIn("-D:C:/Games/Skyrim Special Edition/Data",cmd)
        self.assertIn("-P:C:/MO2/profiles/Test/plugins.txt",cmd)

    def test_build_command_rejects_non_plugin_target(self):
        with self.assertRaises(ValueError):
            MOD.build_command(
                Path("SSEEdit.exe"),
                "not-a-plugin.txt",
                Path("xedit.log"),
            )

    def test_run_check_removes_stale_log_before_launch_and_parses_new_log(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            exe=root/"SSEEdit.exe"
            exe.write_text("fixture",encoding="utf-8")
            log=root/"check.log"
            log.write_text("STALE CLEAN RESULT",encoding="utf-8")

            def fake_run(command,**kwargs):
                self.assertFalse(log.exists())
                log.write_text(BROKEN_LOG,encoding="utf-8")
                return subprocess.CompletedProcess(command,0,"","")

            with patch.object(MOD.subprocess,"run",side_effect=fake_run):
                result=MOD.run_check(exe,"Broken.esp",log)

            self.assertEqual(result["exit_code"],0)
            self.assertEqual(result["report"]["status"],"fail")
            self.assertEqual(
                result["report"]["findings"][0]["category"],
                "unresolved-reference",
            )

    def test_nonzero_process_exit_prevents_clean_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            exe=root/"SSEEdit.exe"
            exe.write_text("fixture",encoding="utf-8")
            log=root/"check.log"

            def fake_run(command,**kwargs):
                log.write_text(CLEAN_LOG,encoding="utf-8")
                return subprocess.CompletedProcess(command,9,"","failure")

            with patch.object(MOD.subprocess,"run",side_effect=fake_run):
                result=MOD.run_check(exe,"CleanPatch.esp",log)

            self.assertEqual(result["report"]["status"],"needs-review")
            self.assertTrue(
                any("exit code was 9" in x for x in result["report"]["issues"])
            )

if __name__=="__main__":
    unittest.main()
