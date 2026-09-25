import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "run_mo2_devbench_runtime",
    ROOT/"run_mo2_devbench_runtime.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

HEALTH={
    "ok":True,
    "pid":4242,
    "port":8920,
    "exe":"SkyrimSE.exe",
    "vr":False,
    "frame":100,
}

def runtime_test():
    return {
        "schema_version":"skyrim-runtime-test-v1",
        "test_id":"devbench-smoke",
        "project_id":"fixture-project",
        "adapter":"devbench",
        "fixture":{"kind":"new-game","destructive_copy_only":True},
        "steps":[{
            "id":"ready",
            "action":"wait until player loaded",
            "driver":{
                "adapter":"devbench",
                "kind":"wait-until",
                "condition":"playerLoaded",
                "timeout_ms":30000,
            },
        }],
        "assertions":[{
            "id":"player-loaded",
            "kind":"health",
            "expected":True,
            "operator":"eq",
            "severity":"BLOCKER",
            "probe":{
                "adapter":"devbench",
                "tool":"inspect",
                "arguments":{"kind":"state"},
                "json_path":"playerLoaded",
            },
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
            "arguments":None,
            "cwd":None,
        },
        "profiles":{
            "template_dir":str(template),
            "disposable_root":str(profiles),
            "profile_name_prefix":"AgentOS",
            "copy_ignores":[],
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
            "session_game_executables":["SkyrimSE.exe"],
            "allow_force_kill_session_game":False,
        },
        "evidence":{
            "log_paths":[str(root/"owned-runtime.log")],
            "crash_paths":[],
            "frame_trace_paths":[],
            "screenshot_dir":None,
            "forbidden_log_patterns":["\\b(?:ERROR|FATAL)\\b"],
            "complete_for_g19":True,
        },
        "timeouts":{
            "launch_seconds":30,
            "scenario_seconds":60,
            "shutdown_seconds":30,
        },
    }

def observation(session):
    return {
        "schema_version":"skyrim-runtime-observation-v1",
        "run_id":session["run_id"],
        "session_token":session["session_token"],
        "observer_id":"devbench-rest",
        "observer_version":"fixture",
        "transport":"REST",
        "captured_at":"2099-01-01T00:00:00+00:00",
        "steps":[{
            "id":"ready",
            "status":"passed",
            "issues":[],
            "evidence":["fixture://ready"],
        }],
        "assertions":[{
            "id":"player-loaded",
            "status":"pass",
            "observed":True,
            "issues":[],
            "evidence":["fixture://player-loaded"],
        }],
        "gates":[],
        "artifacts":[],
        "issues":[],
    }

class FakeProcess:
    def __init__(self,exit_code=0,timeout_once=False):
        self.returncode=None
        self._exit_code=exit_code
        self._timeout_once=timeout_once
        self._wait_calls=0
    def wait(self,timeout=None):
        self._wait_calls+=1
        if self._timeout_once and self._wait_calls==1:
            raise MOD.subprocess.TimeoutExpired(["MO2"],timeout)
        self.returncode=self._exit_code
        return self._exit_code
    def poll(self):
        return self.returncode

class MO2DevBenchRuntimeTests(unittest.TestCase):
    def make_template(self,root):
        template=root/"template"
        template.mkdir()
        (template/"modlist.txt").write_text("+Fixture\n",encoding="utf-8")
        (template/"plugins.txt").write_text("*Fixture.esp\n",encoding="utf-8")
        return template

    def run_with_fakes(self,test,config,process,observer):
        with patch.object(MOD.os,"name","nt"),              patch.object(MOD.MO2,"assert_process_exclusivity"),              patch.object(MOD.subprocess,"Popen",return_value=process),              patch.object(MOD.DB,"wait_for_health",return_value=dict(HEALTH)),              patch.object(MOD.DB,"run_observer",side_effect=observer),              patch.object(MOD.DB,"post_tool",return_value={"queued":True}):
            return MOD.run_session(
                test,
                config,
                run_id="run-1",
                execute=True,
            )

    def test_closed_loop_can_pass_with_clean_logs_and_fresh_observer(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template,retain_on_failure=False)

            def fake_observer(test,session,**kwargs):
                self.assertEqual(kwargs["initial_health"]["pid"],HEALTH["pid"])
                return observation(session)

            result=self.run_with_fakes(
                runtime_test(),
                config,
                FakeProcess(),
                fake_observer,
            )

            self.assertEqual(result["status"],"passed")
            gates={x["gate"]:x for x in result["gates"]}
            self.assertEqual(gates["G19"]["status"],"pass")
            self.assertEqual(gates["G20"]["status"],"not-applicable")
            self.assertEqual(gates["G21"]["status"],"not-applicable")
            self.assertEqual(gates["G26"]["status"],"pass")
            self.assertFalse(Path(result["profile"]["disposable_dir"]).exists())
            self.assertEqual(result["cleanup"]["status"],"passed")
            self.assertTrue(any(
                x.get("kind")=="devbench-session-health"
                for x in result["evidence"]["artifacts"]
            ))

    def test_missing_devbench_observation_never_passes_and_still_shuts_down(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template,retain_on_failure=True)
            process=FakeProcess()
            with patch.object(MOD.os,"name","nt"),                  patch.object(MOD.MO2,"assert_process_exclusivity"),                  patch.object(MOD.subprocess,"Popen",return_value=process),                  patch.object(MOD.DB,"wait_for_health",return_value=dict(HEALTH)),                  patch.object(
                     MOD.DB,"run_observer",
                     side_effect=ValueError("devbench unavailable"),
                 ),                  patch.object(MOD.DB,"post_tool",return_value={"queued":True}) as shutdown:
                result=MOD.run_session(
                    runtime_test(),
                    config,
                    run_id="run-1",
                    execute=True,
                )

            self.assertEqual(result["status"],"needs-review")
            self.assertEqual(process._wait_calls,1)
            shutdown.assert_called_once()
            self.assertTrue(Path(result["profile"]["disposable_dir"]).exists())
            self.assertTrue(
                any("devbench unavailable" in x for x in result["issues"])
            )

    def test_shutdown_timeout_fails_and_retains_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template,retain_on_failure=True)

            def fake_observer(test,session,**kwargs):
                return observation(session)

            result=self.run_with_fakes(
                runtime_test(),
                config,
                FakeProcess(timeout_once=True),
                fake_observer,
            )

            self.assertEqual(result["status"],"failed")
            self.assertTrue(result["launch"]["timed_out"])
            self.assertTrue(Path(result["profile"]["disposable_dir"]).exists())

    def test_force_kill_is_scoped_to_allowlisted_fresh_session_pid(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template,retain_on_failure=True)
            config["process_policy"]["allow_force_kill_session_game"]=True

            def fake_observer(test,session,**kwargs):
                return observation(session)

            kill_result={
                "pid":HEALTH["pid"],
                "exe":HEALTH["exe"],
                "exit_code":0,
                "stdout":"SUCCESS",
                "stderr":"",
                "killed":True,
            }
            with patch.object(MOD.os,"name","nt"),                  patch.object(MOD.MO2,"assert_process_exclusivity"),                  patch.object(
                     MOD.subprocess,"Popen",
                     return_value=FakeProcess(timeout_once=True),
                 ),                  patch.object(MOD.DB,"wait_for_health",return_value=dict(HEALTH)),                  patch.object(MOD.DB,"run_observer",side_effect=fake_observer),                  patch.object(MOD.DB,"post_tool",return_value={"queued":True}),                  patch.object(
                     MOD,"force_kill_session_game",return_value=kill_result
                 ) as killer:
                result=MOD.run_session(
                    runtime_test(),
                    config,
                    run_id="run-1",
                    execute=True,
                )

            killer.assert_called_once()
            self.assertEqual(killer.call_args.args[0]["pid"],HEALTH["pid"])
            self.assertEqual(result["status"],"failed")
            self.assertTrue(any(
                x.get("kind")=="runtime-force-kill"
                for x in result["evidence"]["artifacts"]
            ))

    def test_force_kill_policy_rejects_unexpected_executable(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            template=self.make_template(root)
            config=worker_config(root,template)
            config["process_policy"]["allow_force_kill_session_game"]=True
            bad=dict(HEALTH)
            bad["exe"]="notepad.exe"
            with self.assertRaisesRegex(ValueError,"not in allowed"):
                MOD.validate_session_health_for_termination(bad,config)

if __name__=="__main__":
    unittest.main()
