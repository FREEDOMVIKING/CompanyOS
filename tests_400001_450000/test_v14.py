import tempfile, unittest
from pathlib import Path
from companyos.commercial_operations_v14.engine import CommercialOperationsV14, write_json

class V14Tests(unittest.TestCase):
    def test_quote_and_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            sf = home / "companyos_runtime/storefront_sales_v8_190001_220000"
            crm = home / "companyos_runtime/customer_growth_crm_v13_360001_400000"
            sf.mkdir(parents=True)
            crm.mkdir(parents=True)
            write_json(sf / "catalog.json", {"products": [{
                "product_id": "p1", "name": "Product One", "score": 90,
                "quality_passed": True, "pricing": {"recommended": 59}
            }]})
            write_json(sf / "orders.json", {"orders": []})
            write_json(crm / "crm_index.json", {"customers": {}})
            write_json(crm / "support_tickets.json", {"tickets": []})
            engine = CommercialOperationsV14(home)
            quote = engine.create_quote({
                "customer": {"email": "buyer@example.com"},
                "items": [{"name": "Product One", "quantity": 2, "unit_price": 59}],
                "discount_percent": 10
            })
            self.assertEqual(quote["total"], 106.2)
            state = engine.run_cycle()
            self.assertEqual(state["status"], "commercial_operations_ready")
            self.assertEqual(state["ab_tests_planned"], 1)
            self.assertTrue(state["draft_only_mode"])

if __name__ == "__main__":
    unittest.main()
