import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

ROOT = Path(__file__).resolve().parents[1]


class RouteCalibrationDocLinkTests(unittest.TestCase):
    def test_roadmap_links_design_doc(self):
        doc = ROOT / 'docs/orchestrator-os/self-audit/route-calibration.md'
        roadmap = ROOT / 'projects/personal-agent-os/roadmap/model-infrastructure-manager.md'
        self.assertTrue(doc.is_file())
        self.assertIn('route-calibration.md', roadmap.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
