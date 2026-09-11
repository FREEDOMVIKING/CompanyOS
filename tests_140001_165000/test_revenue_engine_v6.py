import tempfile
import unittest
from pathlib import Path

from companyos.revenue_engine_v6.engine import RevenueEngineV6

class RevenueEngineV6Tests(unittest.TestCase):
    def test_revenue_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            result = RevenueEngineV6(home).run()
            self.assertEqual(result["status"], "ready_for_external_review")
            state = result["state"]
            self.assertTrue(Path(state["workspace"]).exists())
            self.assertTrue(state["quality_passed"])
            self.assertEqual(state["progress_percent"], 90)
            self.assertFalse(state["external_publish"])
            self.assertFalse(state["payment_connected"])

if __name__ == "__main__":
    unittest.main()
