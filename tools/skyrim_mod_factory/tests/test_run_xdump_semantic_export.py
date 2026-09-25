import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "run_xdump_semantic_export",
    ROOT/"run_xdump_semantic_export.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

DUMP="""Iron Sword [WEAP:00012EB7]
  EDID - Editor ID: IronSword
  Model
    MODL - Model Filename: Weapons\\Iron\\IronSword.nif
"""

class RunXDumpSemanticExportTests(unittest.TestCase):
    def load_map(self):
        return {
            "schema_version":"skyrim-load-order-formid-map-v1",
            "full":{"00":"Skyrim.esm","01":"Fixture.esp"},
            "light":{},
        }

    def test_build_command_uses_dump_mode_data_path_and_filter(self):
        cmd=MOD.build_command(
            Path("C:/Tools/SSEEditDump.exe"),
            Path("C:/Data/Fixture.esp"),
            game_mode="SSE",
            data_path=Path("C:/Data"),
            record_filter=["weap","armo"],
        )
        self.assertEqual(cmd[1],"-Dump")
        self.assertIn("-SSE",cmd)
        self.assertIn("-d:C:/Data",cmd)
        self.assertIn("-dr:WEAP,ARMO",cmd)
        self.assertEqual(cmd[-1],"C:/Data/Fixture.esp")

    def test_run_export_clears_stale_outputs_and_emits_canonical_semantics(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            xdump=root/"SSEEditDump.exe"
            plugin=root/"Fixture.esp"
            raw=root/"dump.txt"
            semantic=root/"semantic.json"
            xdump.write_bytes(b"exe")
            plugin.write_bytes(b"plugin")
            raw.write_text("stale",encoding="utf-8")
            semantic.write_text("stale",encoding="utf-8")

            def fake_run(command,**kwargs):
                self.assertFalse(raw.exists())
                self.assertFalse(semantic.exists())
                return subprocess.CompletedProcess(command,0,DUMP,"")

            with patch.object(MOD.subprocess,"run",side_effect=fake_run):
                result=MOD.run_export(
                    xdump,plugin,raw,semantic,
                    load_order_map=self.load_map(),
                )
            self.assertEqual(
                result["document"]["records"][0]["form_key"],
                "012EB7:Skyrim.esm",
            )
            self.assertTrue(raw.exists())
            self.assertTrue(semantic.exists())
            self.assertTrue(
                result["document"]["provenance"][
                    "canonical_cross_load_order_form_keys"
                ]
            )

    def test_empty_success_stdout_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            xdump=root/"SSEEditDump.exe"
            plugin=root/"Fixture.esp"
            xdump.write_bytes(b"exe")
            plugin.write_bytes(b"plugin")
            with patch.object(
                MOD.subprocess,"run",
                return_value=subprocess.CompletedProcess([],0,"",""),
            ):
                with self.assertRaises(ValueError):
                    MOD.run_export(
                        xdump,plugin,root/"raw.txt",root/"semantic.json"
                    )

    def test_invalid_record_filter_rejected(self):
        with self.assertRaises(ValueError):
            MOD.build_command(
                Path("xDump.exe"),Path("Fixture.esp"),
                record_filter=["TOO-LONG"],
            )

if __name__=="__main__":
    unittest.main()
