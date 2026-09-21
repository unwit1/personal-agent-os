"""Vendor-neutral execution boundary: a worker cannot skip pre/postflight."""
from __future__ import annotations

from typing import Protocol

from .contracts import PROVIDER_RESULT, validate_contract
from .lifecycle import abort_task, begin_task, finish_task


class Provider(Protocol):
    def execute(self, request: dict) -> dict: ...


class GatewayError(RuntimeError):
    def __init__(self, task_id: str, stage: str, exit_code: int = 1):
        super().__init__(f"Task {task_id} failed during {stage}; inspect task-status for recovery")
        self.task_id, self.stage, self.exit_code = task_id, stage, exit_code


def run(query: str, provider: Provider, *, source_client: str = "gateway", reviewer=None, **options) -> dict:
    envelope = begin_task(query, source_client, **options)
    task_id = envelope["task_id"]
    stage = "execution"
    try:
        result = provider.execute({"request": query, "envelope": envelope,
                                   "instructions": "Agent OS owns this task lifecycle; do not start or finish a second task. Follow project-local policy. Return response and structured postflight. Use only explicit decision summaries, never hidden chain-of-thought. Propose evidenced engineering changes, improvements, memories and skills where useful. Mark sanitized true only for abstract engineering metadata, never personal/source document content.",
                                   "result_schema": PROVIDER_RESULT})
        validate_contract(result, PROVIDER_RESULT, "worker result")
        stage = "postflight"
        postflight = finish_task(task_id, result["postflight"], reviewer=reviewer)
        return {"task_id": task_id, "response": result["response"], "postflight": postflight,
                "exit_code": 0 if postflight["outcome"] == "completed" else 3}
    except BaseException as exc:
        classification = "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "timeout" if isinstance(exc, TimeoutError) else "postflight_failed" if stage == "postflight" else "execution_failed"
        abort_task(task_id, stage=stage, error_class=classification)
        code = 130 if classification == "interrupted" else getattr(exc, "exit_code", 1)
        raise GatewayError(task_id, stage, code) from None
