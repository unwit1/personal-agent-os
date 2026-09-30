"""Session foreman: sizing, budget-bounded GPU lifecycle, engine routing, and
the judgement/efficiency eval's scoring. No network, no spend: RunPod,
Hugging Face and the vLLM endpoint are a scripted fake."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator import budget, foreman_deploy as fd, foreman_eval as fe  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.engine import Orchestrator  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402
from agent_os.orchestrator.store import RunStore  # noqa: E402
from agent_os.telemetry import LocalTelemetryStore  # noqa: E402

from test_orchestrator import PASS, OrchestratorFixture, provider  # noqa: E402

HF_INFO = {"id": "org/coder-7b", "sha": "abc123def4567890", "gated": False, "pipeline_tag": "text-generation", "tags": ["license:apache-2.0"],
           "safetensors": {"parameters": {"BF16": 7_000_000_000}, "total": 7_000_000_000},
           "siblings": [{"rfilename": "model-00001.safetensors"}, {"rfilename": "config.json"}], "config": {"model_type": "qwen2"}}
HF_CONFIG = {"num_hidden_layers": 28, "num_attention_heads": 28, "num_key_value_heads": 4, "hidden_size": 3584, "max_position_embeddings": 32768}
OFFERS = [
    {"provider": "runpod", "gpu_id": "NVIDIA RTX A4000", "name": "RTX A4000", "vram_gb": 16, "tier": "community", "usd_per_hour": 0.35},
    {"provider": "runpod", "gpu_id": "NVIDIA RTX A5000", "name": "RTX A5000", "vram_gb": 24, "tier": "community", "usd_per_hour": 0.50},
    {"provider": "runpod", "gpu_id": "NVIDIA RTX 3090", "name": "RTX 3090", "vram_gb": 24, "tier": "community", "usd_per_hour": 0.60},
    {"provider": "runpod", "gpu_id": "NVIDIA A100 80GB PCIe", "name": "A100 PCIe", "vram_gb": 80, "tier": "secure", "usd_per_hour": 1.60},
]


class _Response(io.BytesIO):
    def __init__(self, status: int, payload) -> None:
        super().__init__(json.dumps(payload).encode())
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _TextResponse(io.BytesIO):
    status = 200

    def __init__(self, text: str) -> None:
        super().__init__(text.encode())

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeCloud:
    """Hugging Face + RunPod REST + the pod's vLLM server."""

    def __init__(self, *, ready_after: int = 2, refuse_gpus: tuple[str, ...] = (), crash_log: str | None = None, uptimes: list[int] | None = None) -> None:
        self.ready_after = ready_after
        self.crash_log = crash_log
        self.uptimes = list(uptimes or [])
        self.refuse_gpus = refuse_gpus
        self.pods: dict[str, dict] = {}
        self.deleted: list[str] = []
        self.created: list[dict] = []
        self.model_polls = 0

    def __call__(self, request, timeout=None):
        url, method = request.full_url, request.get_method()
        body = json.loads(request.data.decode()) if request.data else None
        if url.startswith(fd.HF_API):
            return _Response(200, HF_INFO)
        if url.endswith("/config.json"):
            return _Response(200, HF_CONFIG)
        if url == f"{fd.RUNPOD_REST}/pods" and method == "POST":
            if all(gpu in self.refuse_gpus for gpu in body["gpuTypeIds"]):
                raise urllib.error.HTTPError(url, 500, "no capacity", {}, io.BytesIO(b'{"error":"no instances available"}'))
            pod = {"id": f"pod{len(self.pods) + 1}", "name": body["name"], "desiredStatus": "RUNNING", "costPerHr": 0.5 * body["gpuCount"]}
            self.pods[pod["id"]] = pod
            self.created.append(body)
            return _Response(201, pod)
        if url == f"{fd.RUNPOD_REST}/pods" and method == "GET":
            return _Response(200, list(self.pods.values()))
        if url.startswith(f"{fd.RUNPOD_REST}/pods/"):
            pod_id = url.rsplit("/", 1)[1]
            if method == "DELETE":
                self.deleted.append(pod_id)
                self.pods.pop(pod_id, None)
                return _Response(200, None)
            return _Response(200, self.pods[pod_id]) if pod_id in self.pods else _Response(404, {"error": "not found"})
        if url.endswith("/" + fd.CRASH_LOG):
            if self.crash_log is None:
                raise urllib.error.HTTPError(url, 502, "waiting", {}, io.BytesIO(b"<html>waiting</html>"))
            return _TextResponse(self.crash_log)
        if url == "https://api.runpod.io/graphql":
            uptime = self.uptimes.pop(0) if self.uptimes else None
            return _Response(200, {"data": {"pod": {"runtime": None if uptime is None else {"uptimeInSeconds": uptime}}}})
        if url.endswith("/v1/models"):
            self.model_polls += 1
            return _Response(200, {"data": [{"id": HF_INFO["id"]}]} if self.model_polls >= self.ready_after else {"data": []})
        raise AssertionError(f"unexpected request {method} {url}")


class Clock:
    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class Base(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.budget_home = self.root / "budget"
        self.foreman_home = self.root / "foreman"
        self.secrets = {fd.RUNPOD_SECRET: "rp-key", fd.HF_SECRET: "hf-key"}
        self.registered: list[dict] = []
        self.unregistered: list[str] = []
        self.clock = Clock()
        self.cloud = FakeCloud()
        self.runs: dict[str, dict] = {}

    def manager(self, **extra) -> fd.ForemanManager:
        options = dict(base=self.foreman_home, budget_home=self.budget_home, opener=self.cloud, resolve=self.secrets.get,
                       store_secret=lambda ref, value: self.secrets.__setitem__(ref, value),
                       register=lambda state: self.registered.append(dict(state)), unregister=lambda state: self.unregistered.append(state["provider_id"]),
                       run_loader=lambda run_id: self.runs[run_id], clock=self.clock, sleep=self.clock.sleep, inventory=lambda: list(OFFERS))
        options.update(extra)
        return fd.ForemanManager(**options)


class SizingTests(unittest.TestCase):
    def test_links(self) -> None:
        self.assertEqual(fd.parse_hf_link("https://huggingface.co/org/m-7B/tree/v2")["revision"], "v2")
        self.assertEqual(fd.parse_hf_link("hf.co/org/m?x=1")["repo"], "org/m")
        self.assertEqual(fd.parse_hf_link("org/m"), {"repo": "org/m", "revision": None})
        for bad in ("https://huggingface.co/datasets/org/d", "just-a-name", ""):
            with self.assertRaises(ValueError):
                fd.parse_hf_link(bad)

    def test_sizing_uses_config_kv_shape(self) -> None:
        model = fd.summarize_info(HF_INFO, HF_CONFIG)
        self.assertEqual((model["weight_gb"], model["max_position_embeddings"], model["attention_heads"]), (14.0, 32768, 28))
        self.assertEqual(model["kv_bytes_per_token"], 2 * 2 * 28 * 4 * 128)
        need = fd.vram_needed_gb(model)
        self.assertTrue(18 < need < 24, need)  # 14 GB bf16 weights + small GQA KV cache fits one 24 GB card
        self.assertIsNone(fd.deployable_problem(model))
        gguf = fd.summarize_info({**HF_INFO, "safetensors": None, "siblings": [{"rfilename": "m.Q4.gguf"}]})
        self.assertIn("GGUF", fd.deployable_problem(gguf))

    def test_cheapest_gpu_that_fits_and_budget(self) -> None:
        pick = fd.choose_gpu(OFFERS, 20.0, 5.0)["choice"]
        self.assertEqual((pick["name"], pick["gpu_count"]), ("RTX A5000", 1))  # A4000 (16 GB) is cheaper but too small
        self.assertAlmostEqual(pick["max_hours"], 5.0 * fd.STOP_FRACTION / 0.5, places=2)
        refused = fd.choose_gpu(OFFERS, 20.0, 0.1)
        self.assertIn("job budget is $0.10", refused["error"])
        self.assertIn("error", fd.choose_gpu(OFFERS, 900.0, 100.0))

    def test_tensor_parallel_must_divide_heads(self) -> None:
        # 60 GB: two A5000s would fit, but 2 does not divide 7 heads -> the single A100
        pick = fd.choose_gpu(OFFERS, 40.0, 50.0, heads=7)["choice"]
        self.assertEqual((pick["name"], pick["gpu_count"]), ("A100 PCIe", 1))

    def test_pod_request_pins_revision_and_guards_endpoint(self) -> None:
        model = fd.summarize_info(HF_INFO, HF_CONFIG)
        body = fd.pod_request(model, {**OFFERS[1], "gpu_count": 1, "hourly_usd": 0.5}, "secret-key", "hf-token", "n")
        args = body["dockerStartCmd"]
        self.assertEqual(args[args.index("--revision") + 1], HF_INFO["sha"])
        self.assertNotIn("secret-key", args)  # vLLM logs its argv; the key goes in the environment
        self.assertEqual(body["env"]["VLLM_API_KEY"], "secret-key")
        self.assertEqual(body["dockerEntrypoint"][:2], ["bash", "-c"])
        self.assertEqual(body["ports"], ["8000/http"])
        self.assertNotIn("HF_TOKEN", body["env"])  # public repo: the token never leaves this machine
        gated = fd.pod_request({**model, "gated": True}, {**OFFERS[1], "gpu_count": 1}, "k", "hf-token", "n")
        self.assertEqual(gated["env"]["HF_TOKEN"], "hf-token")


class LifecycleTests(Base):
    def test_deploy_serves_meters_and_stops_before_the_cap(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        self.runs["busy"] = {"state": "RUNNING", "nodes": {"plan": {"state": "RUNNING"}}}  # keeps it from idling out
        manager = self.manager()
        original = manager.sleep
        manager.sleep = lambda seconds: (manager.attach("busy"), original(seconds))
        status = manager.deploy("https://huggingface.co/org/coder-7b", job_cap_usd=1.0, background=False)
        self.assertEqual(status["status"], "stopped")
        self.assertIn("job budget reached", status["detail"])
        self.assertEqual(len(self.registered), 1)
        self.assertEqual(self.registered[0]["status"], "ready")
        self.assertEqual(self.unregistered, [self.registered[0]["provider_id"]])
        self.assertEqual(self.cloud.deleted, ["pod1"])
        self.assertEqual(self.cloud.created[0]["gpuTypeIds"][0], "NVIDIA RTX A5000")
        spent = budget.spent(self.budget_home)
        self.assertLessEqual(spent, 1.0)  # never crosses the job budget
        self.assertGreater(spent, 0.9)  # ...but uses almost all of it
        self.assertAlmostEqual(spent, status["spent_usd"], places=3)
        self.assertNotIn("rp-key", json.dumps(fd.load_state(self.foreman_home)))  # no secret values in state

    def test_vllm_crash_fails_fast_with_its_log_and_deletes_the_pod(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        self.cloud.crash_log = "vLLM exited with code 1\nRuntimeError: CUDA driver version is insufficient for CUDA runtime version\n"
        self.cloud.ready_after = 10**6
        status = self.manager().deploy("org/coder-7b", job_cap_usd=5.0, background=False)
        self.assertEqual(status["status"], "failed")
        self.assertIn("CUDA driver version is insufficient", status["detail"])
        self.assertEqual(self.cloud.deleted, ["pod1"])
        self.assertLess(status["spent_usd"], 0.01)  # first poll, not the 45 minute load timeout

    def test_crash_loop_is_detected_from_uptime_resets(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        self.cloud.ready_after = 10**6
        self.cloud.uptimes = [20, 50, 10, 40, 5]
        status = self.manager().deploy("org/coder-7b", job_cap_usd=5.0, background=False)
        self.assertEqual(status["status"], "failed")
        self.assertIn("crash loop", status["detail"])
        self.assertEqual(self.cloud.deleted, ["pod1"])

    def test_network_blip_is_retried_not_fatal(self) -> None:
        # live 2026-09-29: getaddrinfo failed mid-deploy -> the deployment died and the delete failed too
        budget.set_budget(10, 10, home=self.budget_home)
        cloud = self.cloud
        calls = {"hf": 0, "models": 0}

        def flaky(request, timeout=None):
            url = request.full_url
            if url.startswith(fd.HF_API):
                calls["hf"] += 1
                if calls["hf"] == 1:
                    raise urllib.error.URLError(OSError(11001, "getaddrinfo failed"))
            if url.endswith("/v1/models"):
                calls["models"] += 1
                if calls["models"] == 1:
                    raise urllib.error.URLError(OSError(11001, "getaddrinfo failed"))
            return cloud(request, timeout)

        status = self.manager(opener=flaky).deploy("org/coder-7b", job_cap_usd=0.5, background=False)
        self.assertEqual(len(self.registered), 1)  # it became ready despite the blips
        self.assertEqual(len(self.cloud.created), 1)  # and never rented twice
        self.assertEqual(status["status"], "stopped")
        self.assertEqual(self.cloud.deleted, ["pod1"])

    def test_failed_delete_is_kept_pending_and_retried_until_confirmed(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        fd._save_state({"id": "FMN-7", "kind": "huggingface", "status": "ready", "pod_id": "podP", "provider_id": "foreman-x", "registered": True,
                        "hourly_usd": 1.0, "cap_usd": 5.0, "spent_usd": 0.0, "billed_until_epoch": self.clock.now, "deadline_epoch": self.clock.now + 3600,
                        "runs": [], "model": {"repo": "org/coder-7b"}}, self.foreman_home)
        self.cloud.pods["podP"] = {"id": "podP"}
        down = {"on": True}

        def opener(request, timeout=None):
            if down["on"] and request.get_method() == "DELETE":
                raise urllib.error.URLError("getaddrinfo failed")
            return self.cloud(request, timeout)

        manager = self.manager(opener=opener)
        manager.stop("operator")
        state = fd.load_state(self.foreman_home)
        self.assertEqual(state["status"], fd.PENDING)
        self.assertIn("POD STILL RUNNING", state["detail"])
        self.assertGreater(state["spent_usd"], 0)  # billed while the delete kept failing
        down["on"] = False
        manager.resume()  # e.g. the GUI starting later
        state = fd.load_state(self.foreman_home)
        self.assertEqual(state["status"], "stopped")
        self.assertEqual(self.cloud.deleted, ["podP"])
        self.assertAlmostEqual(budget.spent(self.budget_home), state["spent_usd"], places=3)

    def test_reaper_deletes_a_pod_whose_watchdog_died(self) -> None:
        # live 2026-09-29: the deploy process was killed under memory pressure; the pod kept billing
        budget.set_budget(10, 10, home=self.budget_home)
        base = {"id": "FMN-8", "kind": "huggingface", "status": "ready", "pod_id": "podR", "provider_id": "foreman-x", "registered": True,
                "hourly_usd": 1.0, "cap_usd": 5.0, "spent_usd": 0.0, "billed_until_epoch": self.clock.now, "deadline_epoch": self.clock.now + 7200,
                "runs": [], "model": {"repo": "org/coder-7b"}}
        self.cloud.pods["podR"] = {"id": "podR"}
        fd._save_state({**base, "watchdog_epoch": self.clock.now - 30}, self.foreman_home)
        self.assertFalse(self.manager().reap()["reaped"])  # alive: leave it
        self.clock.now += fd.REAP_AFTER_SECONDS + 60
        result = self.manager().reap()
        self.assertTrue(result["reaped"])
        self.assertEqual(self.cloud.deleted, ["podR"])
        self.assertIn("reaper", fd.load_state(self.foreman_home)["detail"])
        self.assertAlmostEqual(budget.spent(self.budget_home), (fd.REAP_AFTER_SECONDS + 60) / 3600, places=3)  # the unwatched minutes are billed

    def test_reaper_ignores_subscription_foremen(self) -> None:
        self.manager(registry=SUBSCRIPTIONS).use("claude")
        self.clock.now += 10**6
        self.assertFalse(self.manager(registry=SUBSCRIPTIONS).reap()["reaped"])

    def test_refuses_without_an_approved_budget(self) -> None:
        with self.assertRaisesRegex(ValueError, "approved compute budget"):
            self.manager().deploy("org/coder-7b", background=False)
        self.assertEqual(self.cloud.created, [])

    def test_one_request_lists_every_affordable_type_of_a_group_cheapest_first(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        self.manager().deploy("org/coder-7b", job_cap_usd=0.5, background=False)
        body = self.cloud.created[0]
        self.assertEqual((body["gpuTypeIds"], body["gpuTypePriority"], body["gpuCount"]), (["NVIDIA RTX A5000", "NVIDIA RTX 3090"], "custom", 1))

    def test_groups_exclude_types_far_above_the_cheapest(self) -> None:
        offers = [{"gpu_id": gid, "name": gid, "tier": "community", "gpu_count": 1, "hourly_usd": price} for gid, price in (("a", 0.60), ("b", 0.85), ("c", 1.40))]
        self.assertEqual([[item["gpu_id"] for item in group] for group in fd.attempt_groups(offers)], [["a", "b"]])

    def test_falls_back_to_the_next_group_when_a_group_has_no_capacity(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        self.cloud.refuse_gpus = ("NVIDIA RTX A5000", "NVIDIA RTX 3090")  # the whole 1-GPU community group is sold out
        status = self.manager().deploy("org/coder-7b", job_cap_usd=5.0, background=False)
        # the refused request is not recorded; the next group (2x A4000, community) had capacity
        self.assertEqual([(body["gpuTypeIds"], body["gpuCount"]) for body in self.cloud.created], [(["NVIDIA RTX A4000"], 2)])
        self.assertEqual(status["gpu"]["name"], "RTX A4000")
        self.assertEqual(status["status"], "stopped")

    def test_idle_teardown_after_every_attached_run_planned(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        manager = self.manager()
        manager.attach("run-x")  # nothing active yet -> no attachment
        self.runs["run-1"] = {"state": "RUNNING", "nodes": {"plan": {"state": "RUNNING"}}}
        ticks = {"n": 0}

        def sleep(seconds: float) -> None:
            self.clock.sleep(seconds)
            ticks["n"] += 1
            if ticks["n"] == 1:
                manager.attach("run-1")
            if ticks["n"] == 6:
                self.runs["run-1"]["nodes"]["plan"]["state"] = "PASSED"

        manager.sleep = sleep
        status = manager.deploy("org/coder-7b", job_cap_usd=10.0, idle_minutes=5, background=False)
        self.assertEqual(status["status"], "stopped")
        self.assertIn("idle for 5 min", status["detail"])
        self.assertEqual(status["runs"], ["run-1"])
        self.assertLess(status["spent_usd"], 0.2)  # stopped long before the $10 budget

    def test_stop_from_another_process_is_not_undone_by_the_watchdog(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        manager = self.manager()
        other = self.manager()
        ticks = {"n": 0}

        def sleep(seconds: float) -> None:
            self.clock.sleep(seconds)
            ticks["n"] += 1
            if ticks["n"] == 4:
                other.stop("stopped from the CLI")

        manager.sleep = sleep
        manager.deploy("org/coder-7b", job_cap_usd=10.0, background=False)
        state = fd.load_state(self.foreman_home)
        self.assertEqual((state["status"], state["detail"]), ("stopped", "stopped from the CLI"))
        self.assertEqual(self.cloud.deleted, ["pod1"])

    def test_resume_after_restart_enforces_a_passed_deadline(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        self.cloud.pods["podZ"] = {"id": "podZ", "desiredStatus": "RUNNING", "costPerHr": 1.0}
        fd._save_state({"id": "FMN-1", "status": "ready", "pod_id": "podZ", "provider_id": "foreman-x", "hourly_usd": 1.0, "cap_usd": 2.0,
                        "spent_usd": 0.5, "billed_until_epoch": self.clock.now - 3 * 3600, "deadline_epoch": self.clock.now - 3600,
                        "runs": [], "idle_minutes": 15, "model": {"repo": "org/coder-7b"}}, self.foreman_home)
        manager = self.manager(sleep=lambda seconds: None)
        manager.resume()
        manager._thread.join(5)
        state = fd.load_state(self.foreman_home)
        self.assertEqual(state["status"], "stopped")
        self.assertEqual(self.cloud.deleted, ["podZ"])
        self.assertEqual(self.unregistered, ["foreman-x"])

    def test_resume_deletes_an_orphan_pod_created_before_its_id_was_saved(self) -> None:
        fd._save_state({"id": "FMN-2", "status": "provisioning", "runs": [], "model": {"repo": "org/coder-7b"}}, self.foreman_home)
        self.cloud.pods["podO"] = {"id": "podO", "name": "agent-os-foreman-FMN-2"}
        self.cloud.pods["mine"] = {"id": "mine", "name": "someone-elses-pod"}
        self.manager().resume()
        self.assertEqual(self.cloud.deleted, ["podO"])
        self.assertEqual(fd.load_state(self.foreman_home)["status"], "failed")

    def test_planner_hold_states(self) -> None:
        record = {"foreman": {"deployment_id": "FMN-9"}}
        for status, key in (("loading", "wait"), ("ready", "provider"), ("failed", "fallback")):
            fd._save_state({"id": "FMN-9", "status": status, "provider_id": "foreman-x", "model": {"repo": "org/m"}}, self.foreman_home)
            self.assertIn(key, fd.planner_hold(record, self.foreman_home), status)
        self.assertIn("fallback", fd.planner_hold({"foreman": {"deployment_id": "FMN-other"}}, self.foreman_home))


SUBSCRIPTIONS = ProviderRegistry(providers=[
    {"id": "claude-code", "adapter": "claude_code", "models": {"fast": "haiku", "balanced": "sonnet", "reasoning": "opus"}},
    {"id": "codex", "adapter": "codex_cli", "models": {"fast": "gpt-6-luna", "balanced": "gpt-6-sol", "reasoning": "gpt-6.1-sol", "frontier": "gpt-6-astra"}},
], discover=False)


class SourceTests(Base):
    """Claude / ChatGPT subscriptions and local servers as the session foreman."""

    def test_choices_list_each_subscription_and_its_models(self) -> None:
        choices = fd.subscription_choices(SUBSCRIPTIONS)
        self.assertEqual(choices["claude"], {"provider": "claude-code", "default": "opus", "models": ["opus", "sonnet", "haiku"]})
        self.assertEqual(choices["chatgpt"]["default"], "gpt-6.1-sol")
        self.assertIn("gpt-6-astra", choices["chatgpt"]["models"])

    def test_claude_foreman_is_ready_at_once_with_no_rental(self) -> None:
        status = self.manager(registry=SUBSCRIPTIONS).use("claude", model="sonnet")
        self.assertEqual((status["kind"], status["status"], status["provider_id"], status["override_model"]), ("claude", "ready", "claude-code", "sonnet"))
        self.assertEqual((self.cloud.created, self.registered), ([], []))  # nothing rented, nothing registered
        hold = fd.planner_hold({"foreman": {"deployment_id": status["id"]}}, self.foreman_home)
        self.assertEqual((hold["provider"], hold["override_model"]), ("claude-code", "sonnet"))
        self.manager(registry=SUBSCRIPTIONS).stop()
        self.assertEqual(self.unregistered, [])  # never removes your subscription provider

    def test_chatgpt_rejects_a_model_it_does_not_offer(self) -> None:
        with self.assertRaisesRegex(ValueError, "chatgpt offers"):
            self.manager(registry=SUBSCRIPTIONS).use("chatgpt", model="opus")
        self.assertEqual(self.manager(registry=SUBSCRIPTIONS).use("chatgpt")["model"]["repo"], "gpt-6.1-sol")

    def test_missing_subscription_is_explained(self) -> None:
        with self.assertRaisesRegex(ValueError, "no claude provider"):
            self.manager(registry=ProviderRegistry(providers=[], discover=False)).use("claude")

    def test_local_server_is_checked_then_registered_and_removed_on_stop(self) -> None:
        self.cloud.ready_after = 1
        manager = self.manager(registry=SUBSCRIPTIONS)
        status = manager.use("local", base_url="http://127.0.0.1:11434/")
        self.assertEqual((status["provider_id"], status["model"]["repo"], status["base_url"]), (fd.LOCAL_PROVIDER, HF_INFO["id"], "http://127.0.0.1:11434"))
        self.assertEqual([item["provider_id"] for item in self.registered], [fd.LOCAL_PROVIDER])
        with self.assertRaisesRegex(ValueError, "does not serve"):
            manager.use("local", base_url="http://127.0.0.1:11434", model="other/model")
        manager.stop()
        self.assertEqual(self.unregistered, [fd.LOCAL_PROVIDER])

    def test_local_entry_is_a_planner_endpoint_without_rental_fields(self) -> None:
        from agent_os.orchestrator.model_profile import endpoint_entry

        captured = {}

        def fake_add(entry, write=False, force=False):
            captured.update(entry)
            return {"written": True}

        import agent_os.orchestrator.service as service

        original = service.add_model_endpoint
        service.add_model_endpoint = fake_add
        try:
            fd._register_provider({"kind": "local", "provider_id": fd.LOCAL_PROVIDER, "base_url": "http://127.0.0.1:11434", "model": {"repo": "qwen2.5:14b"}, "id": "FMN-1"})
        finally:
            service.add_model_endpoint = original
        self.assertEqual(captured["roles"], ["planner", "inline"])
        self.assertEqual(captured["profile"]["deployment"], "local")
        self.assertNotIn("secret_ref", captured["options"])
        self.assertIsNotNone(endpoint_entry)

    def test_openrouter_foreman_validates_the_model_and_registers_a_per_token_endpoint(self) -> None:
        listing = {"data": [{"id": "qwen/qwen3-235b-a22b-2507", "pricing": {"prompt": "0.000000087", "completion": "0.00000035"}, "context_length": 262144,
                             "supported_parameters": ["tools"], "architecture": {"output_modalities": ["text"]}},
                            {"id": "img/model", "pricing": {"prompt": "0.000001", "completion": "0"}, "architecture": {"output_modalities": ["image"]}}]}
        cloud = self.cloud

        def opener(request, timeout=None):
            if request.full_url == fd.OPENROUTER_BASE + "/v1/models":
                return _Response(200, listing)
            return cloud(request, timeout)

        self.assertEqual([row["id"] for row in fd.openrouter_models(opener)], ["qwen/qwen3-235b-a22b-2507"])  # image model dropped
        manager = self.manager(registry=SUBSCRIPTIONS, opener=opener)
        with self.assertRaisesRegex(ValueError, "API key missing"):
            manager.use("openrouter", model="qwen/qwen3-235b-a22b-2507")
        self.secrets[fd.OPENROUTER_SECRET] = "or-key"
        with self.assertRaisesRegex(ValueError, "does not list"):
            manager.use("openrouter", model="nope/nope")
        status = manager.use("openrouter", model="qwen/qwen3-235b-a22b-2507")
        self.assertEqual((status["kind"], status["provider_id"], status["model"]["usd_per_mtok_in"]), ("openrouter", fd.OPENROUTER_PROVIDER, 0.087))
        self.assertEqual(self.registered[-1]["base_url"], fd.OPENROUTER_BASE)
        self.assertNotIn("or-key", json.dumps(fd.load_state(self.foreman_home)))
        self.assertFalse(manager.reap()["reaped"])  # nothing rented
        manager.stop()
        self.assertEqual(self.unregistered, [fd.OPENROUTER_PROVIDER])

    def test_switching_from_a_rented_pod_deletes_it_first(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        fd._save_state({"id": "FMN-1", "kind": "huggingface", "status": "ready", "pod_id": "podH", "provider_id": "foreman-x", "registered": True,
                        "hourly_usd": 1.0, "cap_usd": 2.0, "spent_usd": 0.1, "billed_until_epoch": self.clock.now, "deadline_epoch": self.clock.now + 3600,
                        "runs": [], "model": {"repo": "org/coder-7b"}}, self.foreman_home)
        self.cloud.pods["podH"] = {"id": "podH"}
        status = self.manager(registry=SUBSCRIPTIONS).use("chatgpt")
        self.assertEqual(self.cloud.deleted, ["podH"])
        self.assertEqual(self.unregistered, ["foreman-x"])
        self.assertEqual((status["kind"], status["provider_id"]), ("chatgpt", "codex"))

    def test_resume_leaves_a_subscription_foreman_alone(self) -> None:
        self.manager(registry=SUBSCRIPTIONS).use("claude")
        self.assertEqual(self.manager(registry=SUBSCRIPTIONS).resume()["status"], "ready")


class EngineRoutingTests(OrchestratorFixture):
    """The foreman plans; its per-task class choices decide which model runs each task."""

    # ids double as scopes: the synthetic worker writes inside <id>/
    PLAN = [
        {"id": "a", "goal": "decide the locking protocol and write it down", "scope": ["a"], "capability_class": "reasoning", "effort": "high"},
        {"id": "b", "goal": "fix a typo", "scope": ["b"], "capability_class": "fast", "effort": "low"},
        {"id": "c", "goal": "implement the protocol", "scope": ["c"], "capability_class": "balanced", "effort": "medium", "depends_on": ["a"]},
    ]

    def setUp(self) -> None:
        super().setUp()
        self.foreman_home = self.tmp / "foreman"
        self.planner_prompts: list[str] = []

        def foreman_script(request, call):
            self.planner_prompts.append(Path(request.prompt_path).read_text(encoding="utf-8"))
            return {"structured": {"status": "done", "summary": "plan", "tasks": self.PLAN}}

        synthetic.SCRIPTS["foreman-coder"] = foreman_script
        registry = ProviderRegistry(providers=[provider("alpha"), provider("foreman-coder", roles=["planner", "inline"], max_concurrency=4)])
        self.engine = Orchestrator(RunStore(self.tmp / "home"), registry=registry, telemetry_store=LocalTelemetryStore(self.telemetry_path),
                                   claims_path=self.claims, sleep=lambda seconds: None, session_foreman=True, foreman_home=self.foreman_home)

    def foreman(self, status: str) -> None:
        fd._save_state({"id": "FMN-1", "status": status, "provider_id": "foreman-coder", "model": {"repo": "org/coder-7b"}, "runs": []}, self.foreman_home)

    def create(self) -> str:
        return self.engine.create_run("add cross-process locking", repository=self.repo, policy=self.policy(require_distinct_review_provider=False, final_integration="branch", default_validators=[PASS]))["run_id"]

    def drive(self, run_id: str, ticks: int = 60) -> dict:
        for _ in range(ticks):
            self.engine.step(run_id)
            record = self.engine.load(run_id)
            if record["state"] in {"COMPLETE", "BLOCKED", "FAILED"}:
                break
        return self.engine.load(run_id)

    def test_foreman_plans_and_each_task_runs_on_the_model_for_its_class(self) -> None:
        self.foreman("ready")
        run_id = self.create()
        self.engine.start(run_id)
        record = self.drive(run_id)
        self.assertEqual(record["state"], "COMPLETE", record.get("state_reason"))
        nodes = record["nodes"]
        self.assertEqual(nodes["plan"]["selection"]["provider"], "foreman-coder")
        routed = {node_id: nodes[node_id]["selection"]["model"] for node_id in ("a", "b", "c")}
        self.assertEqual(routed, {"a": "alpha-reasoning", "b": "alpha-fast", "c": "alpha-balanced"})
        # the foreman plans only: coding roles never route to it
        self.assertTrue(all(node["selection"]["provider"] == "alpha" for node in nodes.values() if node["role"] != "planner" and node.get("selection")))
        self.assertEqual(len(self.planner_prompts), 1)
        self.assertIn("capability_class", self.planner_prompts[0])
        self.assertEqual(fd.load_state(self.foreman_home)["runs"], [run_id])

    def test_run_waits_for_a_loading_foreman_then_uses_it(self) -> None:
        self.foreman("loading")
        run_id = self.create()
        self.engine.start(run_id)
        for _ in range(3):
            self.engine.step(run_id)
        record = self.engine.load(run_id)
        self.assertEqual(record["state"], "PLANNING")  # waiting, not BLOCKED
        self.assertIn("session foreman", record["state_reason"])
        self.assertEqual(self.planner_prompts, [])
        self.foreman("ready")
        record = self.drive(run_id)
        self.assertEqual(record["nodes"]["plan"]["selection"]["provider"], "foreman-coder")
        self.assertEqual(record["state"], "COMPLETE")

    def test_failed_foreman_falls_back_to_the_normal_planner(self) -> None:
        self.foreman("loading")
        run_id = self.create()
        self.foreman("failed")
        self.engine.start(run_id)
        record = self.drive(run_id)
        self.assertEqual(record["nodes"]["plan"]["selection"]["provider"], "alpha")
        self.assertEqual(record["foreman"]["status"], "fallback")
        self.assertEqual(record["state"], "COMPLETE")

    def test_subscription_foreman_with_a_pinned_model_plans_on_that_model(self) -> None:
        fd._save_state({"id": "FMN-2", "kind": "claude", "status": "ready", "provider_id": "foreman-coder", "override_model": "foreman-coder-frontier",
                        "model": {"repo": "foreman-coder-frontier"}, "runs": []}, self.foreman_home)
        run_id = self.create()
        self.engine.start(run_id)
        record = self.drive(run_id)
        self.assertEqual(record["state"], "COMPLETE", record.get("state_reason"))
        self.assertEqual((record["nodes"]["plan"]["selection"]["provider"], record["nodes"]["plan"]["selection"]["model"]), ("foreman-coder", "foreman-coder-frontier"))

    def cool(self, provider_id: str) -> None:
        from datetime import datetime, timedelta, timezone

        from agent_os.orchestrator import provider_health

        until = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(timespec="seconds")
        provider_health.write_cooldown(self.engine.store.home, provider_id, until, "quota: usage limit reached")

    def test_backup_foreman_plans_while_the_foreman_is_at_its_usage_limit(self) -> None:
        fd._save_state({"id": "FMN-3", "kind": "claude", "status": "ready", "provider_id": "foreman-coder", "model": {"repo": "opus"}, "runs": [],
                        "backups": [{"kind": "chatgpt", "provider": "alpha", "model": None}]}, self.foreman_home)
        self.cool("foreman-coder")
        run_id = self.create()
        self.engine.start(run_id)
        record = self.drive(run_id)
        self.assertEqual(record["state"], "COMPLETE", record.get("state_reason"))
        self.assertEqual(record["nodes"]["plan"]["selection"]["provider"], "alpha")
        self.assertEqual(record["foreman"]["backup_for"], "foreman-coder")
        self.assertEqual(self.planner_prompts, [])  # the limited foreman was never called

    def test_every_foreman_limited_means_the_planner_waits_instead_of_failing(self) -> None:
        fd._save_state({"id": "FMN-4", "kind": "claude", "status": "ready", "provider_id": "foreman-coder", "model": {"repo": "opus"}, "runs": [],
                        "backups": [{"kind": "chatgpt", "provider": "alpha", "model": None}]}, self.foreman_home)
        self.cool("foreman-coder")
        self.cool("alpha")
        run_id = self.create()
        self.engine.start(run_id)
        for _ in range(3):
            self.engine.step(run_id)
        record = self.engine.load(run_id)
        self.assertEqual(record["state"], "PLANNING")
        self.assertIn("usage limits", record["state_reason"])

    def test_default_backups_are_the_other_subscriptions(self) -> None:
        self.assertEqual([item["provider"] for item in fd.default_backups("claude-code", SUBSCRIPTIONS)], ["codex"])
        self.assertEqual([item["provider"] for item in fd.default_backups("foreman-qwen", SUBSCRIPTIONS)], ["claude-code", "codex"])

    def test_foreman_plan_is_merged_and_the_strategy_recorded(self) -> None:
        self.PLAN = [{"id": "a", "goal": "part one", "scope": ["a"], "capability_class": "fast"},
                     {"id": "a2", "goal": "part two", "scope": ["a"], "capability_class": "fast"},
                     {"id": "b", "goal": "other", "scope": ["b"], "capability_class": "fast", "depends_on": ["a2"]}]
        self.foreman("ready")
        run_id = self.create()
        self.engine.start(run_id)
        record = self.drive(run_id)
        self.assertEqual(record["state"], "COMPLETE", record.get("state_reason"))
        self.assertNotIn("a2", record["nodes"])
        self.assertIn("a", record["nodes"]["b"]["depends_on"])
        self.assertIn(record["foreman"]["strategy"]["band"], ("weak", "medium", "strong"))

    def test_no_foreman_means_no_attachment(self) -> None:
        run_id = self.create()
        self.assertNotIn("foreman", self.engine.load(run_id))


class EvalScoringTests(unittest.TestCase):
    """The eval's verdicts on canned foreman answers (the live run uses the same scorer)."""

    def setUp(self) -> None:
        self.cases = {case["id"]: case for case in fe.CASES}

    def verdict(self, case_id: str, tasks: list[dict]) -> dict:
        _, record, policy = self._record()
        return fe.score(self.cases[case_id], {"status": "done", "tasks": tasks}, record, policy)

    def _record(self):
        from agent_os.orchestrator import planner
        from agent_os.orchestrator.model import merge_policy

        policy = merge_policy({"planning": "auto"})
        nodes = planner.planner_plan("goal")
        return None, {"run_id": "r", "goal": "goal", "nodes": nodes, "order": list(nodes)}, policy

    def test_right_sized_plan_passes_at_ideal_cost(self) -> None:
        row = self.verdict("docs-typo", [{"id": "t", "goal": "fix", "scope": ["docs/simple-mode.md"], "capability_class": "fast", "effort": "low"}])
        self.assertTrue(row["passed"], row)
        self.assertEqual(row["cost_ratio"], 1.0)

    def test_over_provisioning_is_wasteful(self) -> None:
        row = self.verdict("docs-typo", [{"id": "t", "goal": "fix", "scope": ["docs/simple-mode.md"], "capability_class": "reasoning", "effort": "high"}])
        self.assertFalse(row["passed"])
        self.assertEqual(row["over"], ["t"])
        self.assertEqual(row["cost_ratio"], 4.67)  # (reasoning 6.5 + overhead 0.5) / (fast 1 + overhead 0.5)

    def test_under_provisioning_a_design_task_is_risky(self) -> None:
        tasks = [{"id": "a", "goal": "x", "scope": ["src/a.py"], "capability_class": "fast"}, {"id": "b", "goal": "y", "scope": ["src/b.py"], "capability_class": "fast"}]
        row = self.verdict("concurrency-design", tasks)
        self.assertTrue(row["under"])
        self.assertFalse(row["passed"])
        good = [{**tasks[0], "capability_class": "reasoning", "effort": "high"}, {**tasks[1], "depends_on": ["a"]}]
        self.assertTrue(self.verdict("concurrency-design", good)["passed"])

    def test_invalid_plan_is_not_valid(self) -> None:
        row = self.verdict("cli-flag", [{"id": "t", "goal": "x", "role": "wizard"}])
        self.assertFalse(row["valid"])
        self.assertIn("error", row)

    def test_run_with_scripted_foreman_summarizes(self) -> None:
        def runner(prompt, workdir):
            self.assertIn("no file or shell tools", prompt)
            return {"outcome": "completed", "seconds": 2.0, "usage": {"input_tokens": 1500, "output_tokens": 300},
                    "structured": {"status": "done", "tasks": [{"id": "t", "goal": "g", "scope": ["docs/simple-mode.md"], "capability_class": "fast", "effort": "low"}]}}

        with tempfile.TemporaryDirectory() as out:
            report = fe.run("scripted", runner=runner, cases=["docs-typo", "concurrency-design"], hourly_usd=0.36, out_dir=Path(out))
        summary = report["summary"]
        self.assertEqual(summary["judgement_accuracy"], 0.5)  # all-fast is right for a typo, wrong for concurrency design
        self.assertEqual(summary["under_provisioned_cases"], 1)
        self.assertEqual(summary["failed_cases"], ["concurrency-design"])
        self.assertEqual(summary["gpu_usd_for_calls"], 0.0004)


class GpuAgentTests(unittest.TestCase):
    """The rented model as a coding agent through a Codex CLI custom provider."""

    STATE = {"id": "FMN-9", "kind": "huggingface", "provider_id": "foreman-coder-7b", "base_url": "https://pod1-8000.proxy.runpod.net",
             "model": {"repo": "org/coder-7b", "model_type": "qwen2"}}

    def test_pod_enables_tool_calling_for_known_families(self) -> None:
        model = fd.summarize_info(HF_INFO, HF_CONFIG)
        args = fd.pod_request(model, {**OFFERS[1], "gpu_count": 1}, "k", None, "n")["dockerStartCmd"]
        self.assertEqual(args[args.index("--tool-call-parser") + 1], "hermes")
        unknown = fd.pod_request({**model, "model_type": "exotic"}, {**OFFERS[1], "gpu_count": 1}, "k", None, "n")["dockerStartCmd"]
        self.assertNotIn("--tool-call-parser", unknown)

    def test_agent_entry_routes_codex_to_the_pod_without_the_key_in_config(self) -> None:
        entry = fd.agent_entry(self.STATE)
        self.assertEqual((entry["id"], entry["adapter"], entry["roles"]), ("foreman-coder-7b-agent", "codex_cli", ["implementer", "test_author", "repairer"]))
        self.assertEqual(entry["options"]["extra_config"]["model_providers.agentosgpu.base_url"], "https://pod1-8000.proxy.runpod.net/v1")
        self.assertEqual(entry["options"]["extra_config"]["model_providers.agentosgpu.wire_api"], "responses")
        self.assertEqual(entry["options"]["secret_env"], {fd.GPU_KEY_ENV: fd.ENDPOINT_SECRET})
        self.assertLess(entry["costs"]["fast"], 1.0)
        self.assertIsNone(fd.agent_entry({**self.STATE, "model": {"repo": "x/y", "model_type": "exotic"}}))
        self.assertIsNone(fd.agent_entry({**self.STATE, "kind": "claude"}))

    def test_codex_adapter_passes_extra_config_and_secret_env(self) -> None:
        from agent_os.orchestrator.adapters.base import AgentLaunchRequest
        from agent_os.orchestrator.adapters.codex_cli import CodexCliAdapter

        adapter = CodexCliAdapter(fd.agent_entry(self.STATE))
        with tempfile.TemporaryDirectory() as tmp:
            request = AgentLaunchRequest(run_id="r", node_id="n", role="implementer", cwd=tmp, prompt_path=str(Path(tmp) / "p.md"), output_dir=tmp,
                                         capability_class="fast", effort="low", model="org/coder-7b", provider_effort=None, read_only=False, timeout_seconds=60)
            import agent_os.orchestrator.secret_refs as refs

            saved = refs.resolve
            refs.resolve = lambda ref: "gpu-secret" if ref == fd.ENDPOINT_SECRET else None
            try:
                env = adapter._env(request, adapter.provider["options"])
                try:
                    plan = adapter.resolve_invocation(request)
                except RuntimeError:
                    plan = None  # codex not installed on this machine
            finally:
                refs.resolve = saved
        self.assertEqual(env[fd.GPU_KEY_ENV], "gpu-secret")
        if plan is not None:
            self.assertIn('model_providers.agentosgpu.wire_api="responses"', plan.argv)
            self.assertNotIn("gpu-secret", " ".join(plan.argv) + plan.display)


class UtilizationTests(unittest.TestCase):
    SAMPLE = """# HELP vllm:num_requests_running Number of requests running.
vllm:num_requests_running{model_name="m"} 3.0
vllm:num_requests_waiting{model_name="m"} 0.0
vllm:prompt_tokens_total{model_name="m"} 120000.0
vllm:generation_tokens_total{model_name="m"} 30000.0
vllm:request_success_total{finished_reason="stop",model_name="m"} 40.0
vllm:request_success_total{finished_reason="length",model_name="m"} 2.0
"""

    def test_parse_metrics_sums_labelled_series(self) -> None:
        parsed = fd.parse_metrics(self.SAMPLE)
        self.assertEqual(parsed, {"running": 3.0, "waiting": 0.0, "prompt_tokens": 120000.0, "generation_tokens": 30000.0, "requests": 42.0})

    def test_cost_per_unit(self) -> None:
        view = fd.utilization_view({"spent_usd": 0.6, "usage": {"ticks": 10, "busy_ticks": 4, "generation_tokens": 30000.0, "requests": 42.0}})
        self.assertEqual((view["busy_pct"], view["usd_per_request"], view["usd_per_mtok_generated"], view["idle_usd"]), (40.0, 0.0143, 20.0, 0.36))
        self.assertIsNone(fd.utilization_view({"spent_usd": 1.0}))


class LearnedAvailabilityTests(unittest.TestCase):
    """An invalid_model failure is remembered machine-wide (and expires)."""

    def test_registry_drops_a_learned_unavailable_model_until_it_expires(self) -> None:
        from datetime import datetime, timedelta, timezone

        from agent_os.orchestrator import provider_health

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "providers.json"
            path.write_text(json.dumps({"providers": [{"id": "codex", "adapter": "synthetic", "models": {"reasoning": "gpt-x-sol", "balanced": "gpt-x"}}]}), encoding="utf-8")
            self.assertEqual(ProviderRegistry(path, discover=False).get("codex")["models"]["reasoning"], "gpt-x-sol")
            provider_health.record_unavailable_model(Path(tmp), "codex", "gpt-x-sol", "not supported with a ChatGPT account")
            models = ProviderRegistry(path, discover=False).get("codex")["models"]
            self.assertNotIn("reasoning", models)
            self.assertEqual(models["balanced"], "gpt-x")
            later = datetime.now(timezone.utc) + timedelta(days=8)
            self.assertEqual(provider_health.learned_unavailable(Path(tmp), later), {})


class StrategyTests(unittest.TestCase):
    """Foreman strategy: merge, guard, strength and host detection (no model calls)."""

    SAME_FILE = [{"id": f"t{n}", "goal": f"test case {n}", "scope": ["tests/test_x.py"], "capability_class": "fast", "effort": "low",
                  "validators": ["python -m unittest tests.test_x"]} for n in range(4)]

    def test_same_scope_tasks_merge_into_one(self) -> None:
        from agent_os.orchestrator import foreman_strategy as fs

        tasks = self.SAME_FILE + [{"id": "after", "goal": "use it", "scope": ["src/y.py"], "capability_class": "balanced", "depends_on": ["t2"]}]
        merged, notes = fs.merge_same_scope({"status": "done", "tasks": tasks})
        ids = [task["id"] for task in merged["tasks"]]
        self.assertEqual(ids, ["t0", "after"])
        self.assertEqual(merged["tasks"][1]["depends_on"], ["t0"])  # rewired from the folded t2
        self.assertIn("Then: test case 3", merged["tasks"][0]["goal"])
        self.assertEqual(merged["tasks"][0]["validators"], ["python -m unittest tests.test_x"])
        self.assertEqual(len(notes), 1)

    def test_merge_that_would_create_a_cycle_is_skipped(self) -> None:
        from agent_os.orchestrator import foreman_strategy as fs

        # found live: A (lock.py) -> B (engine.py) -> C (lock.py); folding A and C would loop through B
        tasks = [{"id": "A", "goal": "contract", "scope": ["lock.py"], "capability_class": "reasoning"},
                 {"id": "B", "goal": "use it", "scope": ["engine.py"], "capability_class": "fast", "depends_on": ["A"]},
                 {"id": "C", "goal": "finish", "scope": ["lock.py"], "capability_class": "fast", "depends_on": ["B"]}]
        merged, notes = fs.merge_same_scope({"tasks": tasks})
        self.assertEqual([task["id"] for task in merged["tasks"]], ["A", "B", "C"])
        self.assertIn("cycle", notes[0])

    def test_invented_roles_are_mapped_not_rejected(self) -> None:
        from agent_os.orchestrator import foreman_strategy as fs

        plan = {"tasks": [{"id": "a", "role": "investigator", "goal": "find it", "scope": ["src/w.py"]},
                          {"id": "b", "role": "qa", "goal": "cover it", "scope": ["tests/test_w.py"]},
                          {"id": "c", "role": "implementer", "goal": "x", "scope": ["src/x.py"]}]}
        fixed, notes = fs.normalize_roles(plan)
        self.assertEqual([task["role"] for task in fixed["tasks"]], ["implementer", "test_author", "implementer"])
        self.assertEqual(len(notes), 2)

    def test_merge_keeps_the_strongest_class(self) -> None:
        from agent_os.orchestrator import foreman_strategy as fs

        tasks = [dict(self.SAME_FILE[0]), {**self.SAME_FILE[1], "capability_class": "reasoning", "effort": "high"}]
        merged, _ = fs.merge_same_scope({"tasks": tasks})
        self.assertEqual((merged["tasks"][0]["capability_class"], merged["tasks"][0]["effort"]), ("reasoning", "high"))

    def test_guard_fixes_both_directions(self) -> None:
        from agent_os.orchestrator import foreman_strategy as fs

        plan = {"tasks": [{"id": "a", "goal": "implement the lock file", "scope": ["src/a.py"], "capability_class": "fast"},
                          {"id": "b", "goal": "fix typo in README", "scope": ["README.md"], "capability_class": "reasoning"}]}
        fixed, notes = fs.guard("design cross-process locking for drivers", plan)
        classes = {task["id"]: task["capability_class"] for task in fixed["tasks"]}
        self.assertEqual(classes, {"a": "reasoning", "b": "fast"})
        self.assertEqual(len(notes), 2)
        untouched, none = fs.guard("fix a typo", {"tasks": [{"id": "x", "goal": "typo", "scope": ["a.md"], "capability_class": "fast"}]})
        self.assertEqual(none, [])

    def test_strength_prefers_measurement_then_benchmark_then_tier(self) -> None:
        from agent_os.orchestrator import foreman_strategy as fs

        provider = {"models": {"reasoning": "big", "fast": "small"}}
        self.assertEqual(fs.strength("small", provider=provider)["band"], "weak")
        self.assertEqual(fs.strength("big", provider=provider)["band"], "strong")
        evidence = {"models": {"small": {"benchmarks": {"intelligence_index": 55}}, "big": {"benchmarks": {"intelligence_index": 60}}}}
        self.assertEqual(fs.strength("small", provider=provider, evidence=evidence)["band"], "strong")  # benchmark beats tier
        reports = [{"model": "small", "summary": {"cases": 7, "judgement_accuracy": 0.3, "valid_plans": 0.6}, "cases": []}]
        rated = fs.strength("small", provider=provider, evidence=evidence, reports=reports)
        self.assertEqual(rated["band"], "weak")  # measured judgement beats benchmarks
        self.assertIn("measured", rated["source"])
        self.assertEqual(fs.strength("Qwen2.5-14B-Instruct")["band"], "weak")  # size hint for an unmeasured open model
        self.assertTrue(fs.strategy_for("small", provider=provider)["guard"])

    def test_host_models_read_only_the_model_fields(self) -> None:
        from agent_os.orchestrator import foreman_strategy as fs

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".claude" / "projects" / "p").mkdir(parents=True)
            (home / ".claude" / "projects" / "p" / "s.jsonl").write_text('{"message":{"model":"claude-opus-5-5","content":"secret"}}\n', encoding="utf-8")
            (home / ".codex").mkdir()
            (home / ".codex" / "config.toml").write_text('model = "gpt-6-luna"\nmodel_reasoning_effort = "high"\n', encoding="utf-8")
            found = fs.host_models(home, {"CLAUDECODE": "1", "CLAUDE_EFFORT": "medium"})
        self.assertEqual(found["active"], "claude")
        self.assertEqual((found["hosts"]["claude"]["model"], found["hosts"]["claude"]["effort"]), ("claude-opus-5-5", "medium"))
        self.assertEqual((found["hosts"]["chatgpt"]["model"], found["hosts"]["chatgpt"]["effort"]), ("gpt-6-luna", "high"))
        self.assertNotIn("secret", json.dumps(found))


if __name__ == "__main__":
    unittest.main()
