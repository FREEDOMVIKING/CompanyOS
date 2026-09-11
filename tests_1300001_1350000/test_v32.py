
import tempfile, unittest
from pathlib import Path
from companyos.autonomous_business_operations_v32.engine import AutonomousBusinessOperationsV32, write_json

class V32Tests(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()

            write_json(live/"internet_opportunity_hunter_v27_live.json", {
                "status":"internet_opportunity_hunter_ready",
                "opportunities_discovered":1
            })
            write_json(live/"autonomous_product_builder_v28_live.json", {
                "status":"autonomous_product_builder_ready",
                "products_built":1
            })
            write_json(live/"autonomous_storefront_sales_v29_live.json", {
                "status":"autonomous_storefront_sales_ready",
                "analytics":{"products_total":1,"orders_total":0}
            })
            write_json(live/"autonomous_finance_treasury_v30_live.json", {
                "status":"autonomous_finance_treasury_ready",
                "pnl":{"revenue_usd":0}
            })
            write_json(live/"autonomous_marketing_acquisition_v31_live.json", {
                "status":"autonomous_marketing_acquisition_ready",
                "campaigns_total":1,"leads_total":0
            })
            write_json(live/"autonomous_revenue_expansion_v26_live.json", {
                "status":"autonomous_revenue_expansion_ready",
                "top_venture":"Test Venture"
            })
            write_json(live/"autonomous_specialist_workforce_v24_live.json", {
                "status":"autonomous_specialist_workforce_ready"
            })

            state = AutonomousBusinessOperationsV32(home).run_cycle()
            self.assertEqual(state["status"], "autonomous_business_operations_ready")
            self.assertEqual(state["operations_health_percent"], 100)
            self.assertEqual(state["workflow_count"], 7)
            self.assertGreaterEqual(state["queued_internal_tasks"], 1)
            self.assertFalse(state["automatic_external_actions_enabled"])

if __name__ == "__main__":
    unittest.main()
