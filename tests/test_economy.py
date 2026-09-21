from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.economy import compare_economy_paths, context_economy_report, evaluate_skill_corpus
from agent_os.skills import Skill, match


class SkillEconomyRegressionTests(unittest.TestCase):
    def test_fixed_representative_corpus_selects_only_expected_skills(self) -> None:
        corpus_path = Path(__file__).resolve().parent / "fixtures" / "economy-corpus.json"
        cases = json.loads(corpus_path.read_text(encoding="utf-8"))
        skills = [
            Skill("scanner-debug", "scanner date regression debugging", Path("scanner"), "fixture"),
            Skill("drive-crawl", "Google Drive archive crawl resumable batch", Path("drive"), "fixture"),
            Skill("icloud-import", "iCloud mail import backfill", Path("icloud"), "fixture"),
            Skill("artifact-zip", "artifact ZIP generation validation", Path("zip"), "fixture"),
            Skill("focused-fix", "focused code fix targeted repository search", Path("fix"), "fixture"),
            Skill("research", "research-heavy source evidence review", Path("research"), "fixture"),
            Skill("staged-workflow", "long running multistep workflow", Path("staged"), "fixture"),
        ]
        for result in evaluate_skill_corpus(cases, skills):
            self.assertEqual(result["selected"], result["expected_active"], result["case_id"])
            self.assertTrue(set(result["selected"]).isdisjoint(result["expected_dormant"]), result["case_id"])

    def test_deterministic_ab_comparison_requires_validation_parity(self) -> None:
        baseline = {"context_tokens": 900, "model_calls": 2, "repeated_work": 1, "retries": 1, "escalations": 1, "wall_clock_ms": 100, "highest_capability": "balanced", "validation_passed": True}
        economy = {"context_tokens": 500, "model_calls": 1, "repeated_work": 0, "retries": 0, "escalations": 0, "wall_clock_ms": 80, "highest_capability": "fast", "validation_passed": True}
        report = compare_economy_paths(baseline, economy)
        self.assertTrue(report["quality_parity"])
        self.assertEqual(report["outcome"], "savings_with_validation")
        economy["validation_passed"] = False
        self.assertEqual(compare_economy_paths(baseline, economy)["outcome"], "validation_regression")

    def test_weak_overlap_is_omitted_at_the_context_threshold(self) -> None:
        skills = [Skill("weak", "workflow notes", Path("weak.md"), "test")]
        self.assertEqual(match("workflow", skills, minimum_score=2), [])

    def test_many_unrelated_skills_do_not_displace_the_exact_match(self) -> None:
        skills = [Skill("scanner-regression", "scanner date regression", Path("target.md"), "test")]
        skills.extend(Skill(f"noise-{index}", f"unrelated astronomy token {index}", Path(f"noise-{index}.md"), "test") for index in range(200))
        self.assertEqual(match("fix scanner date regression", skills, minimum_score=2)[0].name, "scanner-regression")

    def test_compiled_context_reports_a_no_model_economy_baseline(self) -> None:
        report = context_economy_report("personal-agent-os", "fix JSON RPC stdio server error", 900)
        self.assertTrue(report["within_budget"])
        self.assertFalse(report["full_skill_bodies_loaded"])
        self.assertLessEqual(report["matched_skill_count"], 3)
        self.assertGreater(report["naive_tokens"], report["selective_tokens"])
        self.assertEqual(report["model_calls"], 0)


if __name__ == "__main__":
    unittest.main()
