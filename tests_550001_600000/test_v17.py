import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from companyos.autonomous_operations_v17.engine import AutonomousOperationsV17

class V17Tests(unittest.TestCase):
    @patch("companyos.autonomous_operations_v17.engine.fetch_json")
    def test_operations_cycle(self, fetch):
        fetch.return_value = {"status": "ready"}
        with tempfile.TemporaryDirectory() as td:
            engine = AutonomousOperationsV17(Path(td))
            state = engine.run_cycle()
            self.assertEqual(state["status"], "autonomous_operations_ready")
            self.assertEqual(state["services_alive"], 7)
            self.assertEqual(state["critical_services_down"], 0)
            self.assertEqual(state["operations_health_score"], 100)
            self.assertFalse(state["external_actions_enabled"])
            self.assertTrue(state["scheduled_tasks"])

if __name__ == "__main__":
    unittest.main()
