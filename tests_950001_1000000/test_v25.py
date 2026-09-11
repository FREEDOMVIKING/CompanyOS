
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from companyos.command_center_v25.engine import CommandCenterV25, write_json

class V25Tests(unittest.TestCase):
    @patch("companyos.command_center_v25.engine.fetch_json")
    def test_command_center_snapshot(self, fetch):
        fetch.return_value = {"status": "ready"}
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()
            write_json(live / "enterprise_automation_v15_live.json", {
                "kpis": {"orders_total": 2, "paid_orders": 1, "revenue_usd": 49, "customers": 1}
            })
            write_json(live / "autonomous_specialist_workforce_v24_live.json", {
                "agents_total": 10, "tasks_completed": 10, "tasks_total": 10, "tasks_blocked": 0
            })
            write_json(live / "external_venture_launcher_v19_live.json", {
                "ventures_prepared": 1, "top_venture": "Test Venture"
            })
            write_json(live / "validation_launch_director_v20_live.json", {
                "ready_for_launch_review": 1
            })

            engine = CommandCenterV25(home)
            state = engine.snapshot()

            self.assertEqual(state["status"], "companyos_command_center_ready")
            self.assertEqual(state["services_alive"], 18)
            self.assertEqual(state["health_percent"], 100)
            self.assertEqual(state["revenue"]["paid_orders"], 1)
            self.assertEqual(state["workforce"]["agents_total"], 10)
            self.assertFalse(state["external_actions_enabled"])

if __name__ == "__main__":
    unittest.main()
