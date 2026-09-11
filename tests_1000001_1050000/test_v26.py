
import tempfile
import unittest
from pathlib import Path
from companyos.autonomous_revenue_expansion_v26.engine import AutonomousRevenueExpansionV26, write_json

class V26Tests(unittest.TestCase):
    def test_portfolio_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()

            venture = home / "generated_ventures_v19/test-venture"
            venture.mkdir(parents=True)

            write_json(venture / "venture_manifest.json", {
                "venture_id": "test-venture",
                "name": "Test Venture",
                "readiness_score": 90,
                "source_opportunity": {"score": 95}
            })
            write_json(venture / "economics.json", {
                "estimated_gross_margin_percent": 90
            })
            write_json(venture / "offer.json", {
                "price_test_usd": [29, 49, 79]
            })
            write_json(live / "validation_launch_director_v20_live.json", {
                "results": [{
                    "venture_id": "test-venture",
                    "validation_score": 90
                }]
            })
            write_json(live / "autonomous_research_network_v22_live.json", {
                "venture_evidence": {
                    "test-venture": {"external_signal_score": 50}
                }
            })
            write_json(live / "self_improvement_learning_v23_live.json", {
                "pricing_recommendations": [{
                    "venture_id": "test-venture",
                    "recommended_price_usd": 49
                }]
            })
            write_json(live / "enterprise_automation_v15_live.json", {
                "kpis": {"revenue_usd": 0}
            })

            engine = AutonomousRevenueExpansionV26(home)
            state = engine.run_cycle()

            self.assertEqual(state["status"], "autonomous_revenue_expansion_ready")
            self.assertEqual(state["ventures_total"], 1)
            self.assertEqual(state["ventures_promoted"], 1)
            self.assertEqual(state["top_venture"], "Test Venture")
            self.assertFalse(state["automatic_fund_allocation_enabled"])
            self.assertTrue((home / "revenue_expansion_records_v26/portfolio_registry.json").exists())

if __name__ == "__main__":
    unittest.main()
