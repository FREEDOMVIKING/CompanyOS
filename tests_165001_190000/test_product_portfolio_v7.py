import tempfile
import unittest
from pathlib import Path
from companyos.product_portfolio_v7.engine import ProductPortfolioEngineV7

class ProductPortfolioV7Tests(unittest.TestCase):
    def test_portfolio_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            result = ProductPortfolioEngineV7(home).run()
            self.assertEqual(result["status"], "portfolio_ready_for_review")
            self.assertEqual(result["portfolio_size"], 3)
            self.assertEqual(result["marketplace_review_queue_length"], 3)
            self.assertFalse(result["external_publish"])
            self.assertEqual(result["analytics"]["sales_count"], 0)
            for item in result["selected_products"]:
                self.assertTrue(item["quality_passed"])
                self.assertTrue(Path(item["workspace"]).exists())

if __name__ == "__main__":
    unittest.main()
