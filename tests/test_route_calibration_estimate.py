import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agent_os.orchestrator.route_calibration import estimate_cells, calibrate, advise  # noqa: E402


class EstimateCellsTest(unittest.TestCase):
    def test_empty(self):
        result = estimate_cells([])
        self.assertEqual(result, {})

    def test_single_family_single_class_all_pass(self):
        outcomes = [
            {"family": "test", "initial_class": "cheap", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": "low", "provider": "p1"},
            {"family": "test", "initial_class": "cheap", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": "low", "provider": "p1"},
            {"family": "test", "initial_class": "cheap", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": "low", "provider": "p1"},
        ]
        result = estimate_cells(outcomes)

        self.assertIn("test", result)
        self.assertIn("cheap", result["test"])
        cell = result["test"]["cheap"]

        self.assertEqual(cell["n"], 3)
        self.assertEqual(cell["passes"], 3)
        self.assertEqual(cell["unlabeled"], 0)
        self.assertEqual(cell["escalated"], 0)
        self.assertEqual(cell["retries"], 0)
        self.assertEqual(cell["review_required"], 0)
        self.assertFalse(cell["sufficient"])  # 3 < 5

    def test_min_samples_threshold(self):
        outcomes = []
        for i in range(10):
            outcomes.append({
                "family": "f1", "initial_class": "c1", "cheap_route_passed": True,
                "escalations": 0, "retries": 0, "review_clean": True,
                "initial_effort": "low", "provider": "p1"
            })

        result = estimate_cells(outcomes, min_samples=5)
        self.assertTrue(result["f1"]["c1"]["sufficient"])

        result = estimate_cells(outcomes, min_samples=15)
        self.assertFalse(result["f1"]["c1"]["sufficient"])

    def test_beta_posterior_mean(self):
        # n=0: p_pass = (0+1)/(0+2) = 0.5
        outcomes = [
            {"family": "f", "initial_class": "c", "cheap_route_passed": None,
             "escalations": 0, "retries": 0, "review_clean": None,
             "initial_effort": None, "provider": None},
        ]
        result = estimate_cells(outcomes, min_samples=1)
        cell = result["f"]["c"]
        self.assertEqual(cell["n"], 0)
        self.assertEqual(cell["p_pass"], 0.5)

    def test_wilson_lower_bound(self):
        # n=0: wilson_lower should be 0.0
        outcomes = []
        for i in range(1):
            outcomes.append({
                "family": "f", "initial_class": "c", "cheap_route_passed": None,
                "escalations": 0, "retries": 0, "review_clean": None,
                "initial_effort": None, "provider": None
            })
        result = estimate_cells(outcomes, min_samples=1)
        self.assertEqual(result["f"]["c"]["wilson_lower"], 0.0)

    def test_grouping_by_family_and_class(self):
        outcomes = [
            {"family": "f1", "initial_class": "c1", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": None, "provider": None},
            {"family": "f1", "initial_class": "c2", "cheap_route_passed": False,
             "escalations": 0, "retries": 0, "review_clean": False,
             "initial_effort": None, "provider": None},
            {"family": "f2", "initial_class": "c1", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": None, "provider": None},
        ]
        result = estimate_cells(outcomes, min_samples=1)

        self.assertIn("f1", result)
        self.assertIn("f2", result)
        self.assertIn("c1", result["f1"])
        self.assertIn("c2", result["f1"])
        self.assertIn("c1", result["f2"])
        self.assertNotIn("c2", result["f2"])

    def test_none_becomes_unknown(self):
        outcomes = [
            {"family": "f", "initial_class": None, "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": None, "provider": None},
        ]
        result = estimate_cells(outcomes, min_samples=1)
        self.assertIn("unknown", result["f"])
        self.assertNotIn(None, result["f"])

    def test_effort_and_provider_sorting(self):
        outcomes = [
            {"family": "f", "initial_class": "c", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": "high", "provider": "p2"},
            {"family": "f", "initial_class": "c", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": "low", "provider": "p1"},
        ]
        result = estimate_cells(outcomes, min_samples=1)
        cell = result["f"]["c"]

        effort_keys = list(cell["by_effort"].keys())
        provider_keys = list(cell["by_provider"].keys())

        self.assertEqual(effort_keys, sorted(effort_keys))
        self.assertEqual(provider_keys, sorted(provider_keys))

    def test_escalations_retries_review_required(self):
        outcomes = [
            {"family": "f", "initial_class": "c", "cheap_route_passed": True,
             "escalations": 2, "retries": 3, "review_clean": False,
             "initial_effort": "low", "provider": "p"},
            {"family": "f", "initial_class": "c", "cheap_route_passed": True,
             "escalations": 0, "retries": 1, "review_clean": True,
             "initial_effort": "low", "provider": "p"},
        ]
        result = estimate_cells(outcomes, min_samples=1)
        cell = result["f"]["c"]

        self.assertEqual(cell["escalated"], 1)  # 1 node with escalations > 0
        self.assertEqual(cell["retries"], 4)  # 3 + 1
        self.assertEqual(cell["review_required"], 1)  # 1 with review_clean False

    def test_unlabeled_count(self):
        outcomes = [
            {"family": "f", "initial_class": "c", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": None, "provider": None},
            {"family": "f", "initial_class": "c", "cheap_route_passed": None,
             "escalations": 0, "retries": 0, "review_clean": None,
             "initial_effort": None, "provider": None},
            {"family": "f", "initial_class": "c", "cheap_route_passed": None,
             "escalations": 0, "retries": 0, "review_clean": None,
             "initial_effort": None, "provider": None},
        ]
        result = estimate_cells(outcomes, min_samples=1)
        cell = result["f"]["c"]

        self.assertEqual(cell["n"], 1)
        self.assertEqual(cell["unlabeled"], 2)

    def test_sorted_keys(self):
        outcomes = [
            {"family": "z", "initial_class": "b", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": None, "provider": None},
            {"family": "a", "initial_class": "y", "cheap_route_passed": True,
             "escalations": 0, "retries": 0, "review_clean": True,
             "initial_effort": None, "provider": None},
        ]
        result = estimate_cells(outcomes, min_samples=1)

        families = list(result.keys())
        self.assertEqual(families, sorted(families))
        for family in result:
            classes = list(result[family].keys())
            self.assertEqual(classes, sorted(classes))

    def test_p_pass_and_wilson_with_real_numbers(self):
        # 8 passes in 10 labeled outcomes
        outcomes = []
        for i in range(8):
            outcomes.append({
                "family": "f", "initial_class": "c", "cheap_route_passed": True,
                "escalations": 0, "retries": 0, "review_clean": True,
                "initial_effort": "low", "provider": "p1"
            })
        for i in range(2):
            outcomes.append({
                "family": "f", "initial_class": "c", "cheap_route_passed": False,
                "escalations": 1, "retries": 0, "review_clean": False,
                "initial_effort": "low", "provider": "p1"
            })

        result = estimate_cells(outcomes, min_samples=1)
        cell = result["f"]["c"]

        # p_pass = (passes + 1) / (n + 2) = (8 + 1) / (10 + 2) = 9/12 = 0.75
        self.assertEqual(cell["p_pass"], round(9/12, 4))
        self.assertEqual(cell["p_pass"], 0.75)

        # wilson_lower with 8 passes in 10
        self.assertEqual(cell["wilson_lower"], 0.4902)

    def test_p_pass_and_wilson_all_pass(self):
        # All outcomes pass (passes == n)
        outcomes = []
        for i in range(10):
            outcomes.append({
                "family": "f", "initial_class": "c", "cheap_route_passed": True,
                "escalations": 0, "retries": 0, "review_clean": True,
                "initial_effort": "low", "provider": "p1"
            })

        result = estimate_cells(outcomes, min_samples=1)
        cell = result["f"]["c"]

        # p_pass = (10 + 1) / (10 + 2) = 11/12 ≈ 0.9167
        self.assertAlmostEqual(cell["p_pass"], 11/12, places=4)
        self.assertEqual(cell["p_pass"], round(11/12, 4))

        # wilson_lower when all pass should be relatively high
        self.assertGreater(cell["wilson_lower"], 0.7)

    def test_unlabeled_mixed_with_labeled(self):
        # Mix labeled and unlabeled, should only count labeled in n
        outcomes = []
        for i in range(5):
            outcomes.append({
                "family": "f", "initial_class": "c", "cheap_route_passed": True,
                "escalations": 0, "retries": 0, "review_clean": True,
                "initial_effort": "low", "provider": "p1"
            })
        for i in range(3):
            outcomes.append({
                "family": "f", "initial_class": "c", "cheap_route_passed": None,
                "escalations": 0, "retries": 0, "review_clean": None,
                "initial_effort": "low", "provider": "p1"
            })

        result = estimate_cells(outcomes, min_samples=1)
        cell = result["f"]["c"]

        # Should have 5 labeled (passes), 3 unlabeled
        self.assertEqual(cell["n"], 5)
        self.assertEqual(cell["passes"], 5)
        self.assertEqual(cell["unlabeled"], 3)

        # p_pass = (5 + 1) / (5 + 2) = 6/7 ≈ 0.8571
        self.assertEqual(cell["p_pass"], round(6/7, 4))


class CalibrateTest(unittest.TestCase):
    def test_empty_cells(self):
        result = calibrate({})
        self.assertEqual(result["recommended_threshold"], None)
        self.assertEqual(result["reason"], "insufficient_evidence")

    def test_default_grid(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": True,
                    "wilson_lower": 0.95,
                    "n": 10,
                    "passes": 10,
                    "escalated": 0,
                }
            }
        }
        result = calibrate(cells)

        thresholds = [p["threshold"] for p in result["curve"]]
        expected = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
        self.assertEqual(thresholds, expected)

    def test_custom_grid(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": True,
                    "wilson_lower": 0.9,
                    "n": 10,
                    "passes": 10,
                    "escalated": 0,
                }
            }
        }
        result = calibrate(cells, grid=[0.5, 0.9])

        thresholds = [p["threshold"] for p in result["curve"]]
        self.assertEqual(thresholds, [0.5, 0.9])

    def test_all_keep_cheap(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": True,
                    "wilson_lower": 0.95,
                    "n": 10,
                    "passes": 10,
                    "escalated": 5,
                }
            }
        }
        result = calibrate(cells, target=0.9)

        for point in result["curve"]:
            self.assertEqual(point["cheap_share"], 1.0)
            self.assertIsNotNone(point["kept_pass_rate"])
            self.assertEqual(point["escalations_avoided"], 0)

    def test_all_escalate_early(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": False,
                    "wilson_lower": 0.5,
                    "n": 2,
                    "passes": 1,
                    "escalated": 5,
                }
            }
        }
        result = calibrate(cells, target=0.9)

        for point in result["curve"]:
            self.assertEqual(point["cheap_share"], 0.0)
            self.assertIsNone(point["kept_pass_rate"])
            self.assertEqual(point["escalations_avoided"], 5)

    def test_recommended_threshold(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": True,
                    "wilson_lower": 0.92,
                    "n": 100,
                    "passes": 92,
                    "escalated": 0,
                }
            }
        }
        result = calibrate(cells, target=0.9)

        # At threshold 0.90, wilson_lower (0.92) >= 0.90, so kept_pass_rate = 0.92 >= 0.9
        self.assertIsNotNone(result["recommended_threshold"])
        self.assertLessEqual(result["recommended_threshold"], 0.90)

    def test_no_threshold_meets_target(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": True,
                    "wilson_lower": 0.7,
                    "n": 100,
                    "passes": 70,
                    "escalated": 0,
                }
            }
        }
        result = calibrate(cells, target=0.9)

        self.assertIsNone(result["recommended_threshold"])
        self.assertEqual(result["reason"], "no_threshold_meets_target")

    def test_insufficient_evidence(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": False,
                    "wilson_lower": 0.9,
                    "n": 2,
                    "passes": 2,
                    "escalated": 0,
                }
            }
        }
        result = calibrate(cells, target=0.9)

        self.assertIsNone(result["recommended_threshold"])
        self.assertEqual(result["reason"], "insufficient_evidence")

    def test_multiple_cells_pooled(self):
        cells = {
            "f": {
                "c1": {
                    "sufficient": True,
                    "wilson_lower": 0.92,
                    "n": 50,
                    "passes": 46,
                    "escalated": 0,
                },
                "c2": {
                    "sufficient": True,
                    "wilson_lower": 0.92,
                    "n": 50,
                    "passes": 46,
                    "escalated": 0,
                }
            }
        }
        result = calibrate(cells, target=0.9, grid=[0.90])

        point = result["curve"][0]
        self.assertEqual(point["cheap_share"], 1.0)
        self.assertAlmostEqual(point["kept_pass_rate"], 92/100, places=4)


class AdviseTest(unittest.TestCase):
    def test_empty_cells(self):
        result = advise({}, 0.9)
        self.assertEqual(result, {})

    def test_keep_cheap_sufficient_and_high_wilson(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": True,
                    "wilson_lower": 0.95,
                }
            }
        }
        result = advise(cells, 0.9)
        self.assertEqual(result["f"]["c"], "keep_cheap")

    def test_escalate_earlier_sufficient_but_low_wilson(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": True,
                    "wilson_lower": 0.7,
                }
            }
        }
        result = advise(cells, 0.9)
        self.assertEqual(result["f"]["c"], "escalate_earlier")

    def test_insufficient_data_not_sufficient(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": False,
                    "wilson_lower": 0.95,
                }
            }
        }
        result = advise(cells, 0.9)
        self.assertEqual(result["f"]["c"], "insufficient_data")

    def test_multiple_families_and_classes(self):
        cells = {
            "f1": {
                "c1": {
                    "sufficient": True,
                    "wilson_lower": 0.95,
                },
                "c2": {
                    "sufficient": False,
                    "wilson_lower": 0.5,
                }
            },
            "f2": {
                "c1": {
                    "sufficient": True,
                    "wilson_lower": 0.7,
                }
            }
        }
        result = advise(cells, 0.9)

        self.assertEqual(result["f1"]["c1"], "keep_cheap")
        self.assertEqual(result["f1"]["c2"], "insufficient_data")
        self.assertEqual(result["f2"]["c1"], "escalate_earlier")

    def test_threshold_boundary(self):
        cells = {
            "f": {
                "c": {
                    "sufficient": True,
                    "wilson_lower": 0.9,
                }
            }
        }

        # wilson_lower == threshold: should keep_cheap
        result = advise(cells, 0.9)
        self.assertEqual(result["f"]["c"], "keep_cheap")

        # wilson_lower > threshold: should keep_cheap
        result = advise(cells, 0.89)
        self.assertEqual(result["f"]["c"], "keep_cheap")

        # wilson_lower < threshold: should escalate_earlier
        result = advise(cells, 0.91)
        self.assertEqual(result["f"]["c"], "escalate_earlier")


if __name__ == "__main__":
    unittest.main()
