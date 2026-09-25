import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "run_mutagen_semantic_oracle",
    ROOT/"run_mutagen_semantic_oracle.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def semantic_doc():
    return {
        "schema_version":"skyrim-semantic-plugin-v1",
        "plugin":{"mod_key":"Fixture.esp","game_release":"SkyrimSE"},
        "records":[{
            "form_key":"000123:Fixture.esp",
            "signature":"MISC",
            "editor_id":"Fixture",
            "asset_paths":[],
            "fields":{"_mutagen":{"runtime_type":"Fixture"}},
        }],
        "provenance":{
            "producer":"mutagen-semantic-oracle",
            "producer_version":"1.0",
            "form_key_mode":"mutagen-formkey-string",
            "canonical_cross_load_order_form_keys":True,
            "coverage":{
                "semantic_fields":["editor_id","asset_paths"],
                "omissions":["fixture"],
            },
        },
    }

class RunMutagenSemanticOracleTests(unittest.TestCase):
    def test_build_command_is_pinned_project_invocation(self):
        cmd=MOD.build_command(
            Path("Fixture.esp"),
            Path("out.json"),
            release="SkyrimSE",
        )
        self.assertEqual(cmd[0],"dotnet")
        self.assertIn(str(MOD.PROJECT),cmd)
        self.assertEqual(cmd[-1],"SkyrimSE")

    def test_invalid_release_fails_closed(self):
        with self.assertRaises(ValueError):
            MOD.build_command(
                Path("Fixture.esp"),
                Path("out.json"),
                release="NotSkyrim",
            )

    def test_run_oracle_deletes_stale_output_and_validates_new_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            plugin=root/"Fixture.esp"
            plugin.write_bytes(b"fixture")
            output=root/"semantic.json"
            output.write_text('{"stale":true}',encoding="utf-8")

            def fake_run(command,**kwargs):
                self.assertFalse(output.exists())
                output.write_text(
                    json.dumps(semantic_doc()),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command,0,"ok","")

            with patch.object(MOD.subprocess,"run",side_effect=fake_run):
                result=MOD.run_oracle(plugin,output)

            self.assertEqual(
                result["document"]["provenance"]["producer"],
                "mutagen-semantic-oracle",
            )
            self.assertEqual(MOD.schema_errors(result["document"]),[])

    def test_nonzero_process_exit_is_error_even_if_output_exists(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            plugin=root/"Fixture.esp"
            plugin.write_bytes(b"fixture")
            output=root/"semantic.json"

            def fake_run(command,**kwargs):
                output.write_text(
                    json.dumps(semantic_doc()),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command,7,"","boom")

            with patch.object(MOD.subprocess,"run",side_effect=fake_run):
                with self.assertRaises(ValueError):
                    MOD.run_oracle(plugin,output)

if __name__=="__main__":
    unittest.main()
