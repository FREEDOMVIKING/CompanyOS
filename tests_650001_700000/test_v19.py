
import tempfile
import unittest
from pathlib import Path
from companyos.external_venture_launcher_v19.engine import ExternalVentureLauncherV19, write_json

class V19Tests(unittest.TestCase):
    def test_launcher_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()
            write_json(live / "approved_opportunities.json", {
                "opportunities": [{
                    "opportunity_id": "test-venture",
                    "name": "Test Venture",
                    "status": "APPROVED",
                    "score": 88,
                    "summary": "A validated opportunity."
                }]
            })
            engine = ExternalVentureLauncherV19(home)
            state = engine.run_cycle()
            self.assertEqual(state["status"], "external_venture_launcher_ready")
            self.assertEqual(state["ventures_prepared"], 1)
            self.assertFalse(state["external_launch_enabled"])
            self.assertTrue((home / "generated_ventures_v19/test-venture/landing_page.html").exists())

if __name__ == "__main__":
    unittest.main()
