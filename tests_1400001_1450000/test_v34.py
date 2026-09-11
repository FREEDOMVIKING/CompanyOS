
import tempfile, unittest
from pathlib import Path
from companyos.portfolio_orchestrator_v34.engine import PortfolioOrchestratorV34, write_json

class V34Tests(unittest.TestCase):
    def test_portfolio_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()

            write_json(live/"autonomous_revenue_expansion_v26_live.json", {
                "portfolio":[
                    {"venture_id":"v1","name":"Alpha","portfolio_score":85,"action":"GROW"},
                    {"venture_id":"v2","name":"Beta","portfolio_score":60,"action":"VALIDATE"}
                ]
            })
            write_json(live/"autonomous_storefront_sales_v29_live.json", {"catalog":[]})
            write_json(live/"autonomous_finance_treasury_v30_live.json", {"pnl":{"revenue_usd":0}})
            write_json(live/"autonomous_marketing_acquisition_v31_live.json", {"campaigns_total":1})
            write_json(live/"validation_launch_director_v20_live.json", {"ready_for_launch_review":0})
            write_json(live/"autonomous_business_operations_v32_live.json", {"stalled_workflows":0})

            state = PortfolioOrchestratorV34(home).run_cycle()
            self.assertEqual(state["status"], "portfolio_orchestrator_ready")
            self.assertEqual(state["ventures_total"], 2)
            self.assertEqual(state["top_venture"], "Alpha")
            self.assertFalse(state["automatic_capital_reallocation_enabled"])

if __name__ == "__main__":
    unittest.main()
