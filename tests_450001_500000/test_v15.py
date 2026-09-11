import tempfile, unittest
from pathlib import Path
from companyos.enterprise_automation_v15.engine import EnterpriseAutomationV15, write_json

class V15Tests(unittest.TestCase):
    def test_enterprise_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            sf = home / "companyos_runtime/storefront_sales_v8_190001_220000"
            sf.mkdir(parents=True)
            write_json(sf / "catalog.json", {"products": [{
                "product_id": "p1", "name": "Product One", "score": 90,
                "quality_passed": True, "pricing": {"recommended": 59}
            }]})
            write_json(sf / "orders.json", {"orders": [{
                "order_id": "o1", "status": "DELIVERED", "amount_usd": 59
            }]})
            engine = EnterpriseAutomationV15(home)
            state = engine.run_cycle()
            self.assertEqual(state["status"], "enterprise_automation_ready")
            self.assertEqual(state["kpis"]["products"], 1)
            self.assertEqual(state["kpis"]["paid_orders"], 1)
            self.assertFalse(state["external_commitments_enabled"])
            self.assertTrue((home / "enterprise_records_v15/daily_intelligence_latest.json").exists())

if __name__ == "__main__":
    unittest.main()
