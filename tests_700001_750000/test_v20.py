
import tempfile
import unittest
from pathlib import Path
from companyos.validation_launch_director_v20.engine import ValidationLaunchDirectorV20, write_json

class V20Tests(unittest.TestCase):
    def test_validation_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            venture = home / "generated_ventures_v19/test-venture"
            venture.mkdir(parents=True)
            write_json(venture / "venture_manifest.json", {
                "venture_id": "test-venture",
                "name": "Test Venture",
                "readiness_score": 60,
                "source_opportunity": {"score": 90}
            })
            write_json(venture / "branding.json", {
                "venture_name": "Test Venture",
                "tagline": "Useful tools"
            })
            write_json(venture / "offer.json", {
                "primary_offer": "Starter Offer",
                "price_test_usd": [29, 49, 79]
            })
            write_json(venture / "economics.json", {
                "estimated_gross_margin_percent": 90,
                "startup_cost_assumption_usd": 0
            })
            write_json(venture / "launch_checklist.json", {
                "items": [{"step": "review", "done": False}]
            })
            (venture / "landing_page.html").write_text("<html></html>", encoding="utf-8")

            engine = ValidationLaunchDirectorV20(home)
            state = engine.run_cycle()
            self.assertEqual(state["status"], "validation_launch_director_ready")
            self.assertEqual(state["ventures_validated"], 1)
            self.assertEqual(state["ready_for_launch_review"], 1)
            self.assertFalse(state["external_launch_enabled"])

if __name__ == "__main__":
    unittest.main()
