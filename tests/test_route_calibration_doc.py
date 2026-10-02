import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs' / 'orchestrator-os' / 'self-audit' / 'route-calibration.md'
ROADMAP = ROOT / 'projects' / 'personal-agent-os' / 'roadmap' / 'model-infrastructure-manager.md'


class RouteCalibrationDesignDocTests(unittest.TestCase):
    def test_doc_covers_design(self):
        text = DOC.read_text(encoding='utf-8')
        for needle in ('PA-routellm', 'BORROW', 'Wilson', 'min_samples', 'cheap_route_passed',
                       'assert_aggregate_only', 'route-calibration'):
            self.assertIn(needle, text)

    def test_roadmap_links_doc(self):
        self.assertIn('route-calibration.md', ROADMAP.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
