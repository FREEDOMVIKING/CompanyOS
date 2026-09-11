
import tempfile, unittest
from pathlib import Path
from companyos.autonomous_marketing_acquisition_v31.engine import AutonomousMarketingAcquisitionV31, write_json

class V31Tests(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()

            write_json(live / "autonomous_storefront_sales_v29_live.json", {
                "catalog": [{
                    "product_id": "p1",
                    "name": "Test Template Kit",
                    "product_type": "digital_template_bundle",
                    "price_usd": 49
                }]
            })

            engine = AutonomousMarketingAcquisitionV31(home)
            state = engine.run_cycle()

            self.assertEqual(state["status"], "autonomous_marketing_acquisition_ready")
            self.assertEqual(state["campaigns_total"], 1)
            self.assertEqual(state["campaigns"][0]["analytics"]["campaign_score"], 50)
            self.assertFalse(state["automatic_ad_spend_enabled"])
            self.assertFalse(state["automatic_posting_enabled"])

if __name__ == "__main__":
    unittest.main()
