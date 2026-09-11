import tempfile, unittest
from pathlib import Path
from companyos.executive_intelligence_v16.engine import ExecutiveIntelligenceV16, write_json

class V16Tests(unittest.TestCase):
    def test_executive_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()
            write_json(live / "autonomous_revenue_v11_live.json", {
                "status": "autonomous_revenue_pipeline_ready",
                "updated_at": "2026-08-06T00:00:00+00:00"
            })
            write_json(live / "autonomous_sales_marketing_v12_live.json", {
                "status": "autonomous_sales_marketing_ready",
                "campaigns_ready": 3,
                "updated_at": "2026-08-06T00:00:00+00:00"
            })
            write_json(live / "customer_growth_crm_v13_live.json", {
                "status": "customer_growth_crm_ready",
                "customers_total": 0,
                "updated_at": "2026-08-06T00:00:00+00:00"
            })
            write_json(live / "commercial_operations_v14_live.json", {
                "status": "commercial_operations_ready",
                "support_drafts": 0,
                "updated_at": "2026-08-06T00:00:00+00:00"
            })
            write_json(live / "enterprise_automation_v15_live.json", {
                "status": "enterprise_automation_ready",
                "kpis": {"products": 3, "paid_orders": 0, "customers": 0},
                "venture_priorities": [{
                    "venture_id": "v1",
                    "name": "Digital Template Business",
                    "status": "ACTIVE",
                    "priority_score": 90
                }],
                "updated_at": "2026-08-06T00:00:00+00:00"
            })

            engine = ExecutiveIntelligenceV16(home)
            state = engine.run_cycle()
            self.assertEqual(state["status"], "executive_intelligence_ready")
            self.assertEqual(state["top_opportunity"], "Digital Template Business")
            self.assertFalse(state["external_actions_enabled"])
            self.assertTrue(state["bottlenecks"])

if __name__ == "__main__":
    unittest.main()
