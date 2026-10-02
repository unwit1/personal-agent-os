"""pod_request throughput flags and weight-volume options (IMP-0015)."""
from __future__ import annotations

import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator import budget, foreman_deploy as fd  # noqa: E402

from test_foreman_deploy import HF_CONFIG, HF_INFO, OFFERS, Base  # noqa: E402

H100 = {"provider": "runpod", "gpu_id": "NVIDIA H100 80GB HBM3", "name": "H100", "vram_gb": 80, "tier": "secure", "gpu_count": 1, "hourly_usd": 2.5}
A5000 = {**OFFERS[1], "gpu_count": 1, "hourly_usd": 0.5}


def _flag(args: list[str], name: str) -> str:
    return args[args.index(name) + 1]


class PodRequestTuningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = fd.summarize_info(HF_INFO, HF_CONFIG)

    def test_throughput_flags_present_after_existing_flags(self) -> None:
        args = fd.pod_request(self.model, A5000, "k", None, "n")["dockerStartCmd"]
        self.assertIn("--enable-prefix-caching", args)
        self.assertIn("--enable-chunked-prefill", args)
        self.assertGreaterEqual(int(_flag(args, "--max-num-seqs")), 4)
        self.assertEqual(_flag(args, "--gpu-memory-utilization"), "0.90")
        self.assertLess(args.index("--tensor-parallel-size"), args.index("--enable-prefix-caching"))
        self.assertNotIn("--kv-cache-dtype", args)  # A5000 has no fp8 KV support

    def test_fp8_kv_cache_on_h100(self) -> None:
        args = fd.pod_request(self.model, H100, "k", None, "n")["dockerStartCmd"]
        self.assertEqual(_flag(args, "--kv-cache-dtype"), "fp8")

    def test_overrides_are_honoured(self) -> None:
        body = fd.pod_request(self.model, H100, "k", None, "n", vllm_overrides={
            "gpu_memory_utilization": 0.8, "max_num_seqs": 7, "prefix_caching": False, "kv_cache_dtype": None})
        args = body["dockerStartCmd"]
        self.assertEqual(_flag(args, "--gpu-memory-utilization"), "0.8")
        self.assertEqual(_flag(args, "--max-num-seqs"), "7")
        self.assertNotIn("--enable-prefix-caching", args)
        self.assertIn("--enable-chunked-prefill", args)
        self.assertNotIn("--kv-cache-dtype", args)

    def test_lower_utilization_shrinks_computed_max_num_seqs(self) -> None:
        model = {**self.model, "kv_bytes_per_token": 200000, "weight_gb": 10}
        base = int(_flag(fd.pod_request(model, H100, "k", None, "n")["dockerStartCmd"], "--max-num-seqs"))
        low = int(_flag(fd.pod_request(model, H100, "k", None, "n", vllm_overrides={"gpu_memory_utilization": 0.5})["dockerStartCmd"], "--max-num-seqs"))
        self.assertLess(low, base)

    def test_choice_without_vram_falls_back_to_floor(self) -> None:
        args = fd.pod_request(self.model, {"gpu_id": "g", "gpu_count": 1, "tier": "community"}, "k", None, "n")["dockerStartCmd"]
        self.assertEqual(_flag(args, "--max-num-seqs"), "4")

    def test_volume_fields_only_when_requested(self) -> None:
        plain = fd.pod_request(self.model, A5000, "k", "hf", "n")
        self.assertEqual(plain["volumeInGb"], 0)
        self.assertNotIn("networkVolumeId", plain)
        self.assertNotIn("HF_HOME", plain["env"])
        cached = fd.pod_request({**self.model, "gated": True}, A5000, "k", "hf", "n", weight_volume="vol123")
        self.assertEqual(cached["networkVolumeId"], "vol123")
        self.assertEqual(cached["volumeMountPath"], "/runpod-volume")
        self.assertEqual(cached["volumeInGb"], 0)
        self.assertEqual(cached["env"]["HF_HOME"], "/runpod-volume/hf")
        self.assertEqual(cached["env"]["VLLM_API_KEY"], "k")
        self.assertEqual(cached["env"]["HF_TOKEN"], "hf")


class DeployThreadingTests(Base):
    def test_deploy_threads_options_into_pod_and_state(self) -> None:
        budget.set_budget(10, 10, home=self.budget_home)
        self.manager().deploy("org/coder-7b", job_cap_usd=1.0, background=False,
                              vllm_overrides={"max_num_seqs": 9}, weight_volume="vol9")
        body = self.cloud.created[0]
        self.assertEqual(_flag(body["dockerStartCmd"], "--max-num-seqs"), "9")
        self.assertEqual(body["networkVolumeId"], "vol9")
        state = fd.load_state(self.foreman_home)
        self.assertEqual(state["vllm_overrides"], {"max_num_seqs": 9})
        self.assertEqual(state["weight_volume"], "vol9")


def _metrics_text(running: int, waiting: int, kv: float, hits: int = 0, queries: int = 0) -> str:
    lines = [f"vllm:num_requests_running {running}", f"vllm:num_requests_waiting {waiting}", f"vllm:gpu_cache_usage_perc {kv}",
             f"vllm:prefix_cache_hits_total {hits}", f"vllm:prefix_cache_queries_total {queries}", ""]
    return chr(10).join(lines)


class _Text:
    status = 200

    def __init__(self, text: str) -> None:
        self.text = text

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None

    def read(self) -> bytes:
        return self.text.encode()


class AdaptiveConcurrencySampleTests(Base):
    def setUp(self) -> None:
        super().setUp()
        self.texts: list[str] = []
        self.retunes: list[int] = []
        self.manager_ = self.manager(opener=lambda request, timeout=None: _Text(self.texts.pop(0)),
                                     retune=lambda state, limit: self.retunes.append(limit))
        self.state = {"id": "FMN-C", "kind": "huggingface", "status": "ready", "pod_id": "p", "provider_id": "foreman-x", "registered": True,
                      "base_url": "http://pod", "hourly_usd": 1.0, "cap_usd": 2.0, "spent_usd": 0.0}
        fd._save_state(self.state, self.foreman_home)

    def sample(self, text: str) -> dict:
        self.texts.append(text)
        self.state = self.manager_._sample(self.state)
        return self.state

    def test_limit_rises_with_spare_kv_then_falls_on_queueing(self) -> None:
        self.sample(_metrics_text(4, 0, 0.3, 5, 10))
        self.assertEqual(self.retunes, [])  # hysteresis: one sample is not enough
        state = self.sample(_metrics_text(4, 0, 0.3, 8, 20))
        self.assertEqual(self.retunes, [6])
        self.assertEqual(state["concurrency"]["limit"], 6)
        state = self.sample(_metrics_text(6, 3, 0.5))
        self.assertEqual(self.retunes, [6, 4])
        self.assertEqual(state["concurrency"]["limit"], 4)

    def test_retune_only_on_change_and_history_recorded(self) -> None:
        for _ in range(3):
            self.sample(_metrics_text(1, 0, 0.5))  # not near the limit: hold
        self.assertEqual(self.retunes, [])
        self.assertFalse(self.state["concurrency"].get("history"))
        self.sample(_metrics_text(4, 0, 0.95))
        history = self.state["concurrency"]["history"]
        self.assertEqual([(h["from"], h["to"], h["reason"]) for h in history], [(4, 2, "backoff_kv")])

    def test_history_is_capped_and_usage_extended(self) -> None:
        for index in range(60):
            self.sample(_metrics_text(4, 0, 0.99) if index % 2 == 0 else _metrics_text(2, 0, 0.1))
        self.assertLessEqual(len(self.state["concurrency"]["history"]), 50)
        usage = self.state["usage"]
        self.assertIn("prev", usage)
        self.assertEqual(usage["kv_usage"], 0.1)
        self.sample(_metrics_text(1, 0, 0.2, 7, 9))
        self.sample(_metrics_text(1, 0, 0.2, 3, 4))
        self.assertEqual((self.state["usage"]["prefix_hits"], self.state["usage"]["prefix_queries"]), (7, 9))
        self.assertEqual(self.state["usage"]["prev"]["prefix_hits"], 3)

    def test_retune_failure_keeps_usage_and_limit(self) -> None:
        def boom(state, limit):
            raise RuntimeError("registry locked")

        self.manager_.retune = boom
        self.sample(_metrics_text(4, 0, 0.3, 5, 10))
        state = self.sample(_metrics_text(4, 0, 0.3, 8, 20))
        self.assertEqual(state["usage"]["ticks"], 2)
        self.assertEqual(state["concurrency"]["limit"], 4)
        self.assertTrue(state["concurrency"]["history"][-1]["failed"])

    def test_default_retune_with_no_matching_entry_is_a_failure(self) -> None:
        from unittest import mock

        self.manager_.retune = fd._retune_provider
        with mock.patch("agent_os.capabilities.load_providers", return_value={"providers": []}):
            self.sample(_metrics_text(4, 0, 0.3, 5, 10))
            state = self.sample(_metrics_text(4, 0, 0.3, 8, 20))
        self.assertEqual(state["concurrency"]["limit"], 4)
        self.assertTrue(state["concurrency"]["history"][-1]["failed"])

    def test_default_retune_rejects_error_or_unwritten_results(self) -> None:
        from unittest import mock

        providers = {"providers": [{"id": "foreman-x", "max_concurrency": 4}]}
        for result in ({"error": "bad"}, {"written": False}):
            with mock.patch("agent_os.capabilities.load_providers", return_value=providers), \
                    mock.patch("agent_os.orchestrator.service.add_model_endpoint", return_value=result):
                with self.assertRaises(RuntimeError):
                    fd._retune_provider(self.state, 6)
        with mock.patch("agent_os.capabilities.load_providers", return_value=providers), \
                mock.patch("agent_os.orchestrator.service.add_model_endpoint", return_value={"written": True}) as add:
            fd._retune_provider(self.state, 6)
        self.assertEqual(add.call_args.args[0]["max_concurrency"], 6)

    def test_unregistered_and_local_skip_the_controller(self) -> None:
        for patch in ({"registered": False}, {"kind": "local"}):
            self.state = {**self.state, **patch, "concurrency": None}
            for _ in range(3):
                self.sample(_metrics_text(4, 0, 0.3))
            self.assertEqual(self.retunes, [])
            self.assertFalse(self.state.get("concurrency"))
            self.assertGreater(self.state["usage"]["ticks"], 0)

    def test_parse_metrics_delegates(self) -> None:
        parsed = fd.parse_metrics(_metrics_text(2, 1, 0.4, 3, 6))
        self.assertEqual((parsed["running"], parsed["kv_usage"], parsed["prefix_queries"]), (2, 0.4, 6))
        self.assertIs(fd.METRICS, fd.vllm_metrics_parser.METRICS)


class KeepBusyTests(Base):
    """Queued useful work holds off the idle teardown; budget, deadline and reaper paths still fire."""

    def setUp(self) -> None:
        super().setUp()
        budget.set_budget(10, 10, home=self.budget_home)
        self.cloud.pods["podK"] = {"id": "podK", "desiredStatus": "RUNNING", "costPerHr": 1.0}
        self.backfill: list[dict] = []
        self.metrics = _metrics_text(0, 0, 0.1)

        def opener(request, timeout=None):
            if request.full_url.endswith("/metrics"):
                return _Text(self.metrics)
            return self.cloud(request, timeout)

        self.manager_ = self.manager(opener=opener, sleep=self.clock.sleep, backfill_loader=lambda: self.backfill)
        self.state = {"id": "FMN-K", "kind": "huggingface", "status": "ready", "pod_id": "podK", "provider_id": "foreman-k", "base_url": "http://pod",
                      "hourly_usd": 1.0, "cap_usd": 5.0, "spent_usd": 0.0, "billed_until_epoch": self.clock.now, "last_needed_epoch": self.clock.now,
                      "deadline_epoch": self.clock.now + 6 * 3600, "runs": ["run-1"], "idle_minutes": 5, "model": {"repo": "org/coder-7b"}}
        # Role coverage (reviewer on the rented endpoint) is a separate node; model it by extending the shared list.
        patcher = mock.patch.object(fd, "ENDPOINT_ROLES", ("planner", "inline", "reviewer"))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.runs["run-1"] = {"state": "RUNNING", "nodes": {"plan": {"state": "PASSED"}, "rev": {"role": "reviewer", "state": "PENDING"}}}
        fd._save_state(self.state, self.foreman_home)

    def watch(self) -> dict:
        self.manager_._watch(self.state)
        return fd.load_state(self.foreman_home)

    def test_queued_review_blocks_idle_teardown_past_idle_minutes(self) -> None:
        ticks = {"n": 0}

        self.metrics = _metrics_text(2, 0, 0.3)  # the router is sending the queued work here

        def sleep(seconds: float) -> None:
            self.clock.sleep(seconds)
            ticks["n"] += 1
            if ticks["n"] == 30:  # 15 minutes: three times idle_minutes
                self.runs["run-1"]["nodes"]["rev"]["state"] = "PASSED"
                self.metrics = _metrics_text(0, 0, 0.1)

        self.manager_.sleep = sleep
        state = self.watch()
        self.assertGreaterEqual(ticks["n"], 30)
        self.assertEqual(state["status"], "stopped")
        self.assertIn("idle for 5 min", state["detail"])
        self.assertFalse(state.get("keep_busy"))  # cleared once nothing was queued

    def test_no_idle_teardown_while_routable_work_is_queued(self) -> None:
        self.clock.now += 20 * 60  # four times idle_minutes with the GPU idle
        self.assertFalse(self.manager_._idle(self.state))
        self.assertEqual(self.state["last_needed_epoch"], self.clock.now)
        self.clock.now += 20 * 60
        self.assertFalse(self.manager_._idle(self.state))

    def test_work_the_provider_has_no_role_for_does_not_hold_the_gpu(self) -> None:
        self.runs["run-1"]["nodes"]["rev"]["role"] = "security_reviewer"
        self.clock.now += 20 * 60
        self.assertTrue(self.manager_._idle(self.state))
        self.assertFalse(self.state.get("keep_busy"))

    def test_registered_roles_come_from_the_registered_entries(self) -> None:
        self.assertEqual(fd.registered_roles({"model": {"repo": "org/coder-7b"}}), {"planner", "inline", "reviewer"} | set(
            (fd.agent_entry({"model": {"repo": "org/coder-7b"}}) or {}).get("roles") or ()))
        self.assertEqual(fd.registered_roles({"roles": ["x"]}), {"planner", "inline", "reviewer"})

    def test_keep_busy_state_records_kind_count_and_reason(self) -> None:
        self.clock.now += 20 * 60
        self.assertFalse(self.manager_._idle(self.state))
        self.assertEqual(self.state["keep_busy"], {"kind": "review", "count": 1, "reason": "1 reviewer node(s) ready"})
        self.assertEqual(self.state["last_needed_epoch"], self.clock.now)

    def test_empty_queue_still_tears_down(self) -> None:
        self.runs["run-1"]["nodes"]["rev"]["state"] = "PASSED"
        state = self.watch()
        self.assertEqual(state["status"], "stopped")
        self.assertIn("idle for 5 min", state["detail"])
        self.assertEqual(self.cloud.deleted, ["podK"])

    def test_backfill_queue_keeps_gpu_when_no_run_work(self) -> None:
        self.runs["run-1"]["nodes"]["rev"]["state"] = "PASSED"
        self.backfill.append({"id": "b1", "kind": "docs"})
        self.clock.now += 20 * 60
        self.assertFalse(self.manager_._idle(self.state))
        self.assertEqual(self.state["keep_busy"]["kind"], "backfill")

    def test_deadline_tears_down_with_work_queued(self) -> None:
        self.state["deadline_epoch"] = self.clock.now + 120
        fd._save_state(self.state, self.foreman_home)
        state = self.watch()
        self.assertEqual(state["status"], "stopped")
        self.assertIn("job budget reached", state["detail"])
        self.assertEqual(self.cloud.deleted, ["podK"])
        self.assertEqual(self.runs["run-1"]["nodes"]["rev"]["state"], "PENDING")  # the work was still queued

    def test_budget_cap_tears_down_with_work_queued(self) -> None:
        self.state["cap_usd"] = 0.05
        fd._save_state(self.state, self.foreman_home)
        state = self.watch()
        self.assertEqual(state["status"], "stopped")
        self.assertIn("job budget reached", state["detail"])

    def test_paid_idle_seconds_accumulate(self) -> None:
        self.state["keep_busy"] = {"kind": "review", "count": 1, "reason": "x"}
        self.manager_._sample(self.state)
        self.manager_._sample(self.state)
        self.metrics = _metrics_text(2, 0, 0.3)
        self.manager_._sample(self.state)
        paid = self.state["usage"]["paid_idle"]
        self.assertEqual(paid, {"paid_seconds": 3.0 * fd.TICK_SECONDS, "idle_seconds": 2.0 * fd.TICK_SECONDS,
                                "idle_with_work_seconds": 2.0 * fd.TICK_SECONDS})


if __name__ == "__main__":
    unittest.main()
