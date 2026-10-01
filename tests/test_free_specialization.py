import unittest

from agent_os.orchestrator import free_specialization as fs

CATALOG = {"models": [{"slug": "a/proven:free", "revision": "r1"}, {"slug": "b/weak:free"}, {"slug": "c/new:free"}, {"slug": "d/few:free"}]}


def obs(model, passed=True, family="unit_tests", **extra):
    return {"provider": "openrouter", "model_resolved": model, "task_family": family, "validator_passed": passed, "at": "2026-10-01T00:00:00Z", **extra}


def data():
    rows = [obs("a/proven:free", seconds=2) for _ in range(40)]
    rows += [obs("b/weak:free", i % 2 == 0) for i in range(20)]
    rows += [obs("d/few:free") for _ in range(3)]
    rows += [obs("z/paid", True) for _ in range(50)]
    return rows


class SpecializationTests(unittest.TestCase):
    def by_model(self, rows, **kw):
        return {r["model"]: r for r in fs.build_records(rows, CATALOG, **kw)}

    def test_statuses(self):
        recs = self.by_model(data())
        self.assertEqual(recs["a/proven:free"]["status"], "proven")
        self.assertEqual(recs["a/proven:free"]["revision"], "r1")
        self.assertEqual(recs["a/proven:free"]["latency_ms"]["p50"], 2000)
        self.assertEqual(recs["a/proven:free"]["useful_progress_per_request"], 1.0)
        self.assertEqual(recs["b/weak:free"]["status"], "unproven")
        self.assertEqual(recs["d/few:free"]["status"], "canary")

    def test_availability_failures_excluded(self):
        rows = [obs("a/proven:free") for _ in range(40)] + [obs("a/proven:free", False, failure_type="rate_limit:429") for _ in range(30)]
        rec = self.by_model(rows)["a/proven:free"]
        self.assertEqual((rec["n"], rec["pass_rate"], rec["availability_failures"], rec["status"]), (40, 1.0, 30, "proven"))

    def test_ignores_models_outside_catalog(self):
        self.assertNotIn("z/paid", self.by_model(data()))

    def test_rank(self):
        recs = fs.build_records(data(), CATALOG)
        self.assertEqual(fs.rank(recs, "unit_tests"), ["a/proven:free", "d/few:free"])
        self.assertEqual(fs.rank(recs, "other"), [])

    def test_canary_pick_deterministic(self):
        recs = fs.build_records(data(), CATALOG)
        self.assertEqual(fs.canary_pick(recs, "unit_tests", CATALOG, 1.0, "s1"), "c/new:free")
        self.assertEqual(fs.canary_pick(recs, "unit_tests", CATALOG, 1.0, "s1"), fs.canary_pick(recs, "unit_tests", CATALOG, 1.0, "s1"))
        self.assertIsNone(fs.canary_pick(recs, "unit_tests", CATALOG, 0.0, "s1"))
        hits = sum(fs.canary_pick(recs, "unit_tests", CATALOG, 0.2, i) is not None for i in range(500))
        self.assertTrue(50 < hits < 150)
        self.assertNotIn(fs.canary_pick(recs, "unit_tests", CATALOG, 1.0, "x"), ("a/proven:free", "b/weak:free"))


if __name__ == "__main__":
    unittest.main()
