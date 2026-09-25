import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "run_mutagen_semantic_export",
    ROOT/"run_mutagen_semantic_export.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def document():
    return {
        "schema_version":"skyrim-semantic-plugin-v1",
        "plugin":{"mod_key":"Fixture.esp","game_release":"SkyrimSE"},
        "records":[],
        "provenance":{
            "producer":"mutagen-semantic-export",
            "producer_version":"1.0",
            "form_key_mode":"mutagen-formkey-string",
            "canonical_cross_load_order_form_keys":True,
            "coverage":{"semantic_fields":["editor_id","asset_paths"]},
        },
    }

class RunMutagenSemanticExportTests(unittest.TestCase):
    def test_build_command_pins_project_and_release(self):
        cmd=MOD.build_command(
            "dotnet",
            Path("/tool/export.csproj"),
            Path("/mods/Fixture.esp"),
            Path("/run/semantic.json"),
            "SkyrimSE",
        )
        self.assertEqual(cmd[0],"dotnet")
        self.assertEqual(cmd[1:3],["run","--project"])
        self.assertIn("/tool/export.csproj",cmd)
        self.assertEqual(cmd[-3:],[
            "/mods/Fixture.esp",
            "/run/semantic.json",
            "SkyrimSE",
        ])

    def test_run_export_removes_stale_output_and_validates_new_document(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            plugin=root/"Fixture.esp"
            project=root/"export.csproj"
            output=root/"semantic.json"
            plugin.write_bytes(b"plugin")
            project.write_text("<Project />",encoding="utf-8")
            output.write_text("stale",encoding="utf-8")

            def fake_run(command,**kwargs):
                self.assertFalse(output.exists())
                output.write_text(json.dumps(document()),encoding="utf-8")
                return subprocess.CompletedProcess(command,0,"ok","")

            with patch.object(MOD.subprocess,"run",side_effect=fake_run):
                result=MOD.run_export(
                    plugin,output,project=project,dotnet="dotnet"
                )
            self.assertEqual(result["document"]["provenance"]["producer"],
                             "mutagen-semantic-export")

    def test_success_without_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            plugin=root/"Fixture.esp"
            project=root/"export.csproj"
            output=root/"semantic.json"
            plugin.write_bytes(b"plugin")
            project.write_text("<Project />",encoding="utf-8")
            with patch.object(
                MOD.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([],0,"",""),
            ):
                with self.assertRaises(ValueError):
                    MOD.run_export(plugin,output,project=project)

    def test_invalid_provenance_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            plugin=root/"Fixture.esp"
            project=root/"export.csproj"
            output=root/"semantic.json"
            plugin.write_bytes(b"plugin")
            project.write_text("<Project />",encoding="utf-8")
            bad=document()
            bad["provenance"]["canonical_cross_load_order_form_keys"]=False

            def fake_run(command,**kwargs):
                output.write_text(json.dumps(bad),encoding="utf-8")
                return subprocess.CompletedProcess(command,0,"","")

            with patch.object(MOD.subprocess,"run",side_effect=fake_run):
                with self.assertRaises(ValueError):
                    MOD.run_export(plugin,output,project=project)

if __name__=="__main__":
    unittest.main()
