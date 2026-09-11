import json
import tempfile
import unittest
from pathlib import Path
from companyos.storefront_sales_v8.engine import StorefrontSalesEngineV8, write_json

class StorefrontSalesV8Tests(unittest.TestCase):
    def seed(self, home):
        p = home / "generated_products_v7" / "test-product"
        for d in ["sales", "product"]:
            (p/d).mkdir(parents=True, exist_ok=True)
        write_json(p/"product_manifest.json", {
            "product_id":"test-product",
            "name":"Test Product",
            "score":90,
            "pricing":{"recommended":39},
        })
        write_json(p/"validation_report.json", {"passed":True,"state":"READY_FOR_MARKETPLACE_REVIEW"})
        (p/"sales"/"product_page_copy.md").write_text("# Test Product", encoding="utf-8")
        (p/"product"/"file.txt").write_text("hello", encoding="utf-8")

    def test_review_gated_storefront(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            self.seed(home)
            engine = StorefrontSalesEngineV8(home)
            state = engine.run()
            self.assertEqual(state["status"], "storefront_ready")
            self.assertEqual(state["product_count"], 1)
            self.assertFalse(state["public_checkout_enabled"])
            result, code = engine.create_order("test-product", "buyer@example.com")
            self.assertEqual(code, 409)
            self.assertEqual(result["error"], "checkout_not_enabled")
            self.assertTrue((home/"storefront_v8"/"index.html").exists())

if __name__ == "__main__":
    unittest.main()
