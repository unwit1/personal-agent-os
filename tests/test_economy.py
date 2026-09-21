from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.economy import context_economy_report
from agent_os.skills import Skill, match


class SkillEconomyRegressionTests(unittest.TestCase):
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
