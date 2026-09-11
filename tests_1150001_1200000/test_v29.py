
import tempfile
import unittest
from pathlib import Path
from companyos.autonomous_storefront_sales_v29.engine import AutonomousStorefrontSalesV29, write_json

class V29Tests(unittest.TestCase):
    def test_storefront_and_order_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            product = home / "generated_products_v28/test-product/1.0.0"
            product.mkdir(parents=True)
            write_json(product / "product_manifest.json", {
                "product_id": "test-product",
                "name": "Test Product",
                "version": "1.0.0",
                "product_type": "digital_template_bundle",
                "quality_score": 100,
                "state": "READY_FOR_PRODUCT_REVIEW",
                "pricing": {"recommended": 49},
                "external_publish_approved": False,
            })
            (product / "quick_start_guide.html").write_text("<html></html>", encoding="utf-8")
            (product / "editable_tool.csv").write_text("a,b\n1,2\n", encoding="utf-8")

            engine = AutonomousStorefrontSalesV29(home)
            state = engine.run_cycle()
            self.assertEqual(state["status"], "autonomous_storefront_sales_ready")
            self.assertEqual(state["analytics"]["products_total"], 1)

            order = engine.create_order("test-product", "customer@example.com")
            self.assertEqual(order["order_status"], "PENDING_PAYMENT")

            paid = engine.mark_paid(order["order_id"], {
                "verified": True,
                "transaction_id": "abc123",
                "chain": "solana",
            })
            self.assertEqual(paid["payment_status"], "PAID_VERIFIED")
            self.assertTrue(paid["license_key"])
            self.assertFalse(state["public_storefront_enabled"])

if __name__ == "__main__":
    unittest.main()
