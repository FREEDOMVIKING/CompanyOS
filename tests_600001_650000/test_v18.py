
import unittest
from unittest.mock import patch
from companyos.global_executive_dashboard_v18 import server

class DashboardTests(unittest.TestCase):
    @patch("companyos.global_executive_dashboard_v18.server.check")
    def test_snapshot(self, check):
        check.return_value = {
            "name": "x", "port": 1, "url": "x",
            "alive": True, "status": "ready", "latency_ms": 1
        }
        state = server.snapshot()
        self.assertEqual(state["status"], "global_executive_dashboard_ready")
        self.assertEqual(state["health_percent"], 100)

if __name__ == "__main__":
    unittest.main()
