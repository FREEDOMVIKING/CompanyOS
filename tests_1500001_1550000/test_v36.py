
import tempfile, unittest
from pathlib import Path
from companyos.autonomous_launch_director_v36.engine import AutonomousLaunchDirectorV36, write_json

class V36Tests(unittest.TestCase):
    def test_launch_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()

            write_json(live/"portfolio_orchestrator_v34_live.json", {
                "ventures":[{"venture_id":"v1","name":"Digital Template Business","portfolio_score":84}]
            })
            write_json(live/"autonomous_storefront_sales_v29_live.json", {
                "status":"autonomous_storefront_sales_ready",
                "catalog":[{"name":"Digital Template Business"}]
            })
            write_json(live/"autonomous_finance_treasury_v30_live.json", {
                "status":"autonomous_finance_treasury_ready",
                "pnl":{"revenue_usd":0}
            })
            write_json(live/"autonomous_marketing_acquisition_v31_live.json", {
                "status":"autonomous_marketing_acquisition_ready",
                "campaigns_total":1
            })
            write_json(live/"autonomous_business_operations_v32_live.json", {
                "status":"autonomous_business_operations_ready",
                "operations_health_percent":100
            })
            write_json(live/"autonomous_customer_success_v33_live.json", {
                "status":"autonomous_customer_success_ready"
            })
            write_json(live/"validation_launch_director_v20_live.json", {
                "ready_for_launch_review":0
            })

            state = AutonomousLaunchDirectorV36(home).run_cycle()
            self.assertEqual(state["status"], "autonomous_launch_director_ready")
            self.assertEqual(state["ventures_evaluated"], 1)
            self.assertGreaterEqual(state["top_launch_score"], 75)
            self.assertFalse(state["automatic_external_launch_enabled"])

if __name__ == "__main__":
    unittest.main()
