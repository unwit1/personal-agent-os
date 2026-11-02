# --- GLUE START ---
"""Throwaway IMP-0008 spike: EVS-TEST-SELECTION as an Inspect AI task."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from inspect_ai import Task, eval as inspect_eval, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import Score, Target, accuracy, mean, scorer
from inspect_ai.solver import Generate, TaskState, solver

from agent_os.orchestrator import eval as ao_eval
from agent_os.orchestrator.test_selection import ImportGraphSelector

CASES = Path("projects/personal-agent-os/orchestrator-os/evals/cases/development/affected-test-selection.json")
case_file = json.loads(CASES.read_text(encoding="utf-8"))
selector = ImportGraphSelector(ao_eval.resolve_commit(case_file["base_commit"]))


@solver
def agent_os_route():
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        changed = state.metadata["changed_files"]
        state.output.completion = json.dumps(selector.select(changed))
        return state
    return solve


@scorer(metrics=[accuracy(), mean()])
def agent_os_rule():
    async def score(state: TaskState, target: Target) -> Score:
        expected = set(json.loads(target.text))
        got = set(json.loads(state.output.completion))
        result = ao_eval.score_test_selection({"items": [{"id": "x", "tests": sorted(got)}]}, [{"id": "x", "changed_files": [], "expected_tests": sorted(expected)}])
        return Score(value="C" if result["correct"] else "I", answer=state.output.completion, metadata={"recall": result["mean_recall"], "precision": result["mean_precision"]})
    return score


@task
def test_selection():
    samples = [Sample(id=case["id"], input=", ".join(case["changed_files"]), target=json.dumps(case["expected_tests"]), metadata={"changed_files": case["changed_files"]}) for case in case_file["cases"]]
    return Task(dataset=MemoryDataset(samples), solver=agent_os_route(), scorer=agent_os_rule())
# --- GLUE END ---


if __name__ == "__main__":
    import time
    started = time.monotonic()
    logs = inspect_eval(test_selection(), model="mockllm/model", log_dir=".agent-local/inspect-logs", display="none")
    log = logs[0]
    metrics = {name: metric.value for score in log.results.scores for name, metric in score.metrics.items()}
    glue = Path(__file__).read_text(encoding="utf-8").split("# --- GLUE START ---")[1].split("# --- GLUE END ---")[0]
    print(json.dumps({"status": log.status, "samples": log.results.total_samples, "metrics": metrics, "seconds": round(time.monotonic() - started, 1),
                      "glue_lines": len([line for line in glue.splitlines() if line.strip()]), "log_file": log.location}, indent=1))
