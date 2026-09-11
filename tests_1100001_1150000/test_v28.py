
import tempfile
import unittest
from pathlib import Path
from companyos.autonomous_product_builder_v28.engine import AutonomousProductBuilderV28, write_json

class V28Tests(unittest.TestCase):
    def test_product_build_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()

            write_json(live / "approved_opportunities.json", {
                "opportunities": [{
                    "opportunity_id": "estimate-kit",
                    "name": "Contractor Estimate Kit",
                    "status": "APPROVED",
                    "score": 92,
                    "summary": "Editable estimating templates and pricing calculator."
                }]
            })

            engine = AutonomousProductBuilderV28(home)
            state = engine.run_cycle()

            self.assertEqual(state["status"], "autonomous_product_builder_ready")
            self.assertEqual(state["products_built"], 1)
            self.assertEqual(state["products_ready_for_review"], 1)
            product = state["products"][0]
            workspace = Path(product["workspace"])
            self.assertTrue((workspace / "editable_tool.csv").exists())
            self.assertTrue((workspace / "quick_start_guide.html").exists())
            self.assertEqual(product["quality_score"], 100.0)
            self.assertFalse(state["automatic_external_publish_enabled"])

if __name__ == "__main__":
    unittest.main()
