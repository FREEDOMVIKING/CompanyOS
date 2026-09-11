
import tempfile, unittest
from pathlib import Path
from companyos.autonomous_venture_incubator_v35.engine import AutonomousVentureIncubatorV35, write_json

class V35Tests(unittest.TestCase):
    def test_incubator_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()
            write_json(live/"portfolio_orchestrator_v34_live.json", {
                "ventures":[{
                    "venture_id":"v1",
                    "name":"Digital Template Business",
                    "portfolio_score":83.75
                }],
                "concentration":{"concentration_risk":"HIGH"}
            })
            state = AutonomousVentureIncubatorV35(home).run_cycle()
            self.assertEqual(state["status"], "autonomous_venture_incubator_ready")
            self.assertGreaterEqual(state["candidates_total"], 3)
            self.assertGreaterEqual(state["portfolio_handoffs"], 1)
            self.assertFalse(state["automatic_company_formation_enabled"])
            self.assertFalse(state["automatic_external_launch_enabled"])

if __name__ == "__main__":
    unittest.main()
