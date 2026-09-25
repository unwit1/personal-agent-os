import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "run_mo2_runtime_session",
    ROOT/"run_mo2_runtime_session.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def runtime_test(save_path=None):
    fixture={"kind":"new-game","destructive_copy_only":True}
    if save_path is not None:
        fixture={"kind":"save","save_path":str(save_path),"destructive_copy_only":True}
    return {
        "schema_version":"skyrim-runtime-test-v1",
        "test_id":"fixture-smoke",
        "project_id":"fixture-project",
        "adapter":"mo2",
        "fixture":fixture,
        "steps":[{"id":"launch","action":"launch fixture"}],
        "assertions":[{
            "id":"alive",
            "kind":"health",
            "expected":True,
            "operator":"eq",
            "severity":"BLOCKER",
        }],
    }

def worker_config(root,template,*,retain_on_failure=True):
    managed=root/"managed"
    profiles=managed/"profiles"
    runs=managed/"runs"
    evidence=managed/"evidence"
    profiles.mkdir(parents=True)
    runs.mkdir(parents=True)
    evidence.mkdir(parents=True)
    return {
        "schema_version":"skyrim-runtime-worker-config-v1",
        "worker_id":"fixture-worker",
        "platform":"windows",
        "mo2":{
            "executable":"C:/MO2/ModOrganizer.exe",
            "instance":"SkyrimSE",
            "configured_executable":"SKSE",
            "arguments":"-forcesteamloader",
            "cwd":None,
        },
        "profiles":{
            "template_dir":str(template),
            "disposable_root":str(profiles),
            "profile_name_prefix":"AgentOS",
            "copy_ignores":["*.tmp"],
            "required_files":["modlist.txt","plugins.txt"],
        },
        "workspace":{
            "run_root":str(runs),
            "evidence_root":str(evidence),
            "allowed_mutation_roots":[str(managed)],
        },
        "fixture_policy":{
            "save_target_relative":"saves",
            "require_fresh_copy":True,
            "delete_disposable_profile_on_success":True,
            "retain_on_failure":retain_on_failure,
        },
        "process_policy":{
            "exclusive_process_names":["ModOrganizer.exe","SkyrimSE.exe"],
            "reject_existing_mo2_instance":True,
        },
        "evidence":{
            "log_paths":[],
            "crash_paths":[],
            "frame_trace_paths":[],
            "screenshot_dir":None,
        },
        "timeouts":{
            "launch_seconds":30,
            "scenario_seconds":60,
            "shutdown_seconds":30,
        },
    }

class RunMO2RuntimeSessionTests(unittest.TestCase):
    def make_template(self,root):
        template=root/"template"
        template.mkdir()
        (template/"modlist.txt").write_text("+Fixture\n",encoding="utf-8")
        (template/"plugins.txt").write_text("*Fixture.esp\n",encoding="utf-8")
        (template/"ignored.tmp").write_text("ignore",encoding="utf-8")
        return template

    def test_build_command_matches_mo2_cli_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            cmd=MOD.build_mo2_command(config,"AgentOS-fixture-run1")
            self.assertEqual(cmd[0],"C:/MO2/ModOrganizer.exe")
            self.assertEqual(
                cmd[1:],
                [
                    "--instance","SkyrimSE",
                    "--profile","AgentOS-fixture-run1",
                    "run","--executable","SKSE",
                    "--arguments","-forcesteamloader",
                ],
            )

    def test_prepare_session_copies_profile_and_save_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            save=root/"Fixture.ess"
            save.write_bytes(b"save-fixture")
            config=worker_config(root,template)
            result,_=MOD.prepare_session(
                runtime_test(save),
                config,
                run_id="run-1",
                build_id="build-1",
            )
            disposable=Path(result["profile"]["disposable_dir"])
            self.assertTrue((disposable/"modlist.txt").exists())
            self.assertFalse((disposable/"ignored.tmp").exists())
            copied=Path(result["fixture"]["destination"])
            self.assertTrue(copied.exists())
            self.assertEqual(MOD.sha256_file(save),MOD.sha256_file(copied))
            self.assertEqual(result["status"],"prepared")
            self.assertRegex(result["session_token"],r"^[0-9a-f]{64}$")
            self.assertEqual(
                MOD.schema_errors(
                    {k:v for k,v in result.items() if k!="_template_before"},
                    MOD.RESULT_SCHEMA,
                ),
                [],
            )

    def test_prepare_refuses_workspace_outside_allowed_roots(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            config["workspace"]["evidence_root"]=str(root/"outside")
            with self.assertRaises(ValueError):
                MOD.prepare_session(
                    runtime_test(),
                    config,
                    run_id="run-1",
                )

    def test_successful_process_without_observer_remains_needs_review(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template,retain_on_failure=False)

            def fake_run(command,**kwargs):
                return subprocess.CompletedProcess(command,0,"runtime out","")

            with patch.object(MOD.os,"name","nt"),                  patch.object(MOD,"windows_process_names",return_value=set()),                  patch.object(MOD.subprocess,"run",side_effect=fake_run):
                result=MOD.run_session(
                    runtime_test(),
                    config,
                    run_id="run-1",
                    execute=True,
                )

            self.assertEqual(result["status"],"needs-review")
            self.assertTrue(result["launch"]["attempted"])
            self.assertEqual(result["launch"]["exit_code"],0)
            self.assertFalse(Path(result["profile"]["disposable_dir"]).exists())
            gates={x["gate"]:x for x in result["gates"]}
            self.assertEqual(gates["G19"]["status"],"needs-review")
            self.assertEqual(gates["G20"]["status"],"not-applicable")
            self.assertEqual(gates["G21"]["status"],"not-applicable")
            self.assertEqual(gates["G26"]["status"],"needs-review")

    def test_conflicting_process_aborts_before_launch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template,retain_on_failure=False)
            with patch.object(MOD.os,"name","nt"),                  patch.object(
                     MOD,"windows_process_names",
                     return_value={"modorganizer.exe"},
                 ),                  patch.object(MOD.subprocess,"run") as launch:
                result=MOD.run_session(
                    runtime_test(),
                    config,
                    run_id="run-1",
                    execute=True,
                )
            self.assertEqual(result["status"],"aborted")
            launch.assert_not_called()
            self.assertTrue(
                any("conflicting process" in x for x in result["issues"])
            )

    def test_template_mutation_is_detected_during_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template,retain_on_failure=False)
            result,_=MOD.prepare_session(
                runtime_test(),
                config,
                run_id="run-1",
            )
            (template/"plugins.txt").write_text("*Changed.esp\n",encoding="utf-8")
            MOD.finalize_cleanup(result,config,success=False)
            self.assertEqual(result["cleanup"]["status"],"failed")
            self.assertFalse(result["profile"]["restored"])

    def test_performance_and_save_fixture_activate_related_gates(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            save=root/"Fixture.ess"
            save.write_bytes(b"save-fixture")
            test=runtime_test(save)
            test["assertions"].append({
                "id":"frametime",
                "kind":"performance",
                "expected":16.7,
                "operator":"lte",
                "severity":"ERROR",
            })
            result,_=MOD.prepare_session(
                test,
                worker_config(root,template),
                run_id="run-1",
            )
            gates={x["gate"]:x for x in result["gates"]}
            self.assertEqual(gates["G20"]["status"],"needs-review")
            self.assertEqual(gates["G21"]["status"],"needs-review")


    def test_g19_pass_requires_explicit_complete_evidence_config(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            log=root/"captured.log"
            log.write_text("all good",encoding="utf-8")
            source=root/"source.log"
            source.write_text("prior clean log",encoding="utf-8")
            config["evidence"].update({
                "log_paths":[str(source)],
                "forbidden_log_patterns":["\\b(?:ERROR|FATAL)\\b"],
                "complete_for_g19":True,
            })
            gate=MOD.evaluate_g19(
                config,
                [{
                    "path":str(source),
                    "change":"changed",
                    "captured_path":str(log),
                }],
                [],
            )
            self.assertEqual(gate["status"],"pass")

    def test_g19_forbidden_log_signature_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            log=root/"captured.log"
            log.write_text("ERROR fixture exploded",encoding="utf-8")
            source=root/"source.log"
            source.write_text("prior clean log",encoding="utf-8")
            config["evidence"].update({
                "log_paths":[str(source)],
                "forbidden_log_patterns":["\\bERROR\\b"],
                "complete_for_g19":True,
            })
            gate=MOD.evaluate_g19(
                config,
                [{
                    "path":str(source),
                    "change":"changed",
                    "captured_path":str(log),
                }],
                [],
            )
            self.assertEqual(gate["status"],"fail")
            self.assertTrue(gate["evidence"])

    def test_g19_new_crash_artifact_fails_even_without_log_match(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            config["evidence"]["complete_for_g19"]=True
            gate=MOD.evaluate_g19(
                config,
                [],
                [{"path":"Crash-2026-09-25.log","change":"added"}],
            )
            self.assertEqual(gate["status"],"fail")

    def test_g19_incomplete_source_declaration_never_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            config["evidence"].update({
                "log_paths":[str(root/"source.log")],
                "forbidden_log_patterns":["\\bERROR\\b"],
                "complete_for_g19":False,
            })
            gate=MOD.evaluate_g19(config,[],[])
            self.assertEqual(gate["status"],"needs-review")


    def test_g19_complete_claim_with_missing_log_source_needs_review(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            config["evidence"].update({
                "log_paths":[str(root/"missing.log")],
                "forbidden_log_patterns":["\\bERROR\\b"],
                "complete_for_g19":True,
            })
            gate=MOD.evaluate_g19(config,[],[])
            self.assertEqual(gate["status"],"needs-review")
            self.assertTrue(any("no readable file match" in x for x in gate["issues"]))

    def test_empty_existing_crash_directory_can_be_complete_clean_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            crash_dir=root/"crashes"
            crash_dir.mkdir()
            config["evidence"].update({
                "log_paths":[],
                "crash_paths":[str(crash_dir)],
                "complete_for_g19":True,
            })
            gate=MOD.evaluate_g19(config,[],[])
            self.assertEqual(gate["status"],"pass")

    def test_path_matcher_handles_glob_and_directory_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            logs=root/"logs"
            logs.mkdir()
            path=logs/"Crash-1.log"
            path.write_text("fixture",encoding="utf-8")
            self.assertTrue(MOD.path_matches_source(
                str(path),
                str(logs/"Crash-*.log"),
            ))
            self.assertTrue(MOD.path_matches_source(str(path),str(logs)))
            self.assertFalse(MOD.path_matches_source(
                str(path),
                str(root/"other"/"*.log"),
            ))


if __name__=="__main__":
    unittest.main()
