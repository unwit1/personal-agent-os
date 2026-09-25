import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("selector",ROOT/"select_implementation_pattern.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)


PACK={
 "patterns":[
  {
   "pattern_id":"actor-distribution",
   "intent":["give actors spells perks items outfits factions keywords"],
   "preferred_layers":["runtime-patching"],
   "selection":{"preferred":["spid"],"alternatives":["skypatcher"],"conditions":["filters fit"]},
  },
  {
   "pattern_id":"quest-dialogue",
   "intent":["quest stages aliases dialogue scenes packages"],
   "preferred_layers":["quest-dialogue","papyrus"],
   "selection":{"preferred":["creation-kit"],"alternatives":["ckpe"],"conditions":["editor relationships matter"]},
  },
  {
   "pattern_id":"conditional-animation-replacement",
   "intent":["replace animations by actor state equipment keywords conditions"],
   "preferred_layers":["animation"],
   "selection":{"preferred":["oar"],"alternatives":["dar"],"conditions":["graph semantics unchanged"]},
  }
 ]
}


def feature(summary, layers=None, frameworks=None, pattern=None):
    return {
      "feature_id":"f",
      "summary":summary,
      "player_observable_behavior":[summary],
      "acceptance_criteria":[{"id":"a","kind":"runtime","statement":"works"}],
      "implementation":{
        "selected_layers":layers or [],
        "selected_frameworks":frameworks or [],
        **({"selected_pattern":pattern} if pattern else {})
      }
    }


class PatternSelectorTests(unittest.TestCase):
    def test_explicit_pattern_wins(self):
        r=MOD.rank(feature("anything",pattern="quest-dialogue"),PACK)
        self.assertEqual(r["status"],"selected")
        self.assertEqual(r["selected_pattern"],"quest-dialogue")
        self.assertEqual(r["confidence"],"high")

    def test_actor_distribution_routes_to_spid_pattern(self):
        r=MOD.rank(feature(
          "Distribute a perk and spell to matching NPC actors using filters",
          layers=["runtime-patching"],
          frameworks=["spid"]
        ),PACK)
        self.assertEqual(r["selected_pattern"],"actor-distribution")
        self.assertIn(r["confidence"],{"high","medium"})

    def test_animation_replacement_routes_to_oar_pattern(self):
        r=MOD.rank(feature(
          "Replace idle animations based on actor equipment and state",
          layers=["animation"],
          frameworks=["oar"]
        ),PACK)
        self.assertEqual(r["selected_pattern"],"conditional-animation-replacement")

    def test_unknown_explicit_pattern_requires_research(self):
        r=MOD.rank(feature("anything",pattern="does-not-exist"),PACK)
        self.assertEqual(r["status"],"research-required")
        self.assertIsNone(r["selected_pattern"])

    def test_ambiguous_low_signal_does_not_force_choice(self):
        r=MOD.rank(feature("Make something better"),PACK)
        self.assertIn(r["status"],{"research-required","no-match"})
        self.assertIsNone(r["selected_pattern"])


if __name__=="__main__":
    unittest.main()
