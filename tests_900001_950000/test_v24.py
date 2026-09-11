
import tempfile
import unittest
from pathlib import Path
from companyos.autonomous_specialist_workforce_v24.engine import AutonomousSpecialistWorkforceV24, write_json

class V24Tests(unittest.TestCase):
    def test_workforce_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()

            write_json(live / "enterprise_automation_v15_live.json", {
                "top_priority_venture": "Test Venture"
            })
            write_json(live / "self_improvement_learning_v23_live.json", {
                "pricing_recommendations": [{"name": "Test Venture", "recommended_price_usd": 49}]
            })
            write_json(live / "autonomous_research_network_v22_live.json", {
                "network_enabled": False, "evidence_items": 0
            })
            write_json(live / "autonomous_operations_v17_live.json", {
                "operations_health_score": 100
            })
            write_json(live / "validation_launch_director_v20_live.json", {
                "results": [{"name": "Test Venture"}]
            })

            engine = AutonomousSpecialistWorkforceV24(home)
            state = engine.run_cycle()

            self.assertEqual(state["status"], "autonomous_specialist_workforce_ready")
            self.assertEqual(state["agents_total"], 10)
            self.assertEqual(state["tasks_total"], 10)
            self.assertEqual(state["tasks_completed"], 10)
            self.assertFalse(state["automatic_external_actions_enabled"])
            self.assertTrue((home / "workforce_records_v24/shared_memory.json").exists())

if __name__ == "__main__":
    unittest.main()
